import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

API_BASE  = "https://openrouter.ai/api/v1"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR  = Path(__file__).resolve().parent / "runs"

# Answer format: the generator writes gold answers in the old GSM8K style ("#### <number>"),
# but the eval asks models for the modern \boxed{<number>} convention (MATH/AIME, most RL math
# training), which models produce more reliably. Both formats are accepted when scoring; anything
# else that still yields a number is scored separately as OK_FMT / WRONG_FMT.
SYSTEM_PROMPT = (
    "You are a math problem solver. Solve the problem exactly as given. Do not ask for clarification or request it to be rewritten. "
    "Think step by step. "
    "At the end of your response, write your final answer as \\boxed{<number>}.\n"
    "The number should be numeric only (no units, no dollar signs)."
)
# Repeated after the question: on very long responses the system-prompt instruction can fade.
USER_SUFFIX = "\n\nPut your final answer in \\boxed{}."

# --variant -> dataset field holding that presentation of the problem (see the generator)
VARIANT_KEYS = {"ordered": "question", "shuffled": "question_shuffled", "split": "question_split",
                "ordered_nonce": "question_nonce", "shuffled_nonce": "question_shuffled_nonce",
                "split_nonce": "question_split_nonce"}

def load_api_key(path):
    p = Path(path)
    if not p.exists() and not p.is_absolute():
        p = REPO_ROOT / path      # fall back to repo root so the script works from any cwd
    if not p.exists():
        sys.exit(f"API key file not found: {path}")
    return p.read_text().strip()

def parse_number(s):
    r"""'1,234.5' / '\$11.25' / '\frac{45}{4}' / '45/4' / '11.25\text{ dollars}' -> float, else None."""
    s = re.sub(r'\\(?:text|mathrm|textbf|mathbf)\{[^{}]*\}', '', s)   # drop units like \text{ dollars}
    s = re.sub(r'\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}', r'\1/\2', s)
    s = re.sub(r'\\[,!;: ]|\\\$|\\left|\\right|[$,\s()]', '', s)
    s = s.rstrip(".")                                                  # "1234.5." would not parse otherwise
    m = re.fullmatch(r'(-?\d*\.?\d+)(?:/(-?\d*\.?\d+))?', s)
    if not m:
        return None
    try:
        num = float(m.group(1))
        return num / float(m.group(2)) if m.group(2) else num
    except ZeroDivisionError:
        return None

def last_boxed(text):
    r"""Contents of the last \boxed{...}, matching nested braces."""
    start = text.rfind("\\boxed{")
    if start < 0:
        return None
    i = start + len("\\boxed{")
    depth = 1
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j]
    return None

def extract_answer(text):
    """Returns (value, fmt). fmt is "boxed" or "####" when a requested format was used,
    "fallback" when the number came from an "Answer: X" phrase or the last number, None if nothing found."""
    if not text:
        return None, None
    boxed = last_boxed(text)
    if boxed is not None:
        val = parse_number(boxed)
        if val is not None:
            return val, "boxed"
    hashes = re.findall(r'####\s*([-\d,.]+)', text)
    if hashes:
        val = parse_number(hashes[-1])
        if val is not None:
            return val, "####"
    answers = re.findall(r'answer\W{0,6}(?:is\W{0,3})?\$?\s*(-?[\d,]*\.?\d+)', text, re.IGNORECASE)
    tail = re.findall(r'-?\d[\d,]*\.?\d*', text[-300:])
    for cand in answers[-1:] + tail[-1:]:
        val = parse_number(cand)
        if val is not None:
            return val, "fallback"
    return None, None

def gold_answer(text):
    """Gold answers from the generator always end with '#### <number>'."""
    m = re.findall(r'####\s*([-\d,.]+)', text)
    return parse_number(m[-1]) if m else None

def answers_match(pred, gold):
    if pred is None or gold is None:
        return False
    return abs(pred - gold) < 1e-4

def build_body(model, question, max_tokens, reasoning_effort=None, reasoning_tokens=None, no_reasoning=False):
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "usage": {"include": True},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": question + USER_SUFFIX},
        ]
    }
    if not no_reasoning:
        if reasoning_effort is not None:
            body["reasoning"] = {"effort": reasoning_effort}
        else:
            # Default: reasoning on, half of max_tokens. Some providers cap the visible answer at
            # max_tokens - reasoning budget, so a budget near max_tokens truncates the answer.
            body["reasoning"] = {"max_tokens": reasoning_tokens if reasoning_tokens is not None else max(1024, max_tokens // 2)}
    return body

def api_request(api_key, method, path, body=None, timeout=60, retries=5):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API_BASE + path, data=data, method=method,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="replace")
            if e.code == 429 or e.code >= 500:
                wait = 2 ** attempt
                print(f"  HTTP {e.code}, retrying in {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise ValueError(f"HTTP {e.code}: {err}")
        except (urllib.error.URLError, TimeoutError) as e:
            wait = 2 ** attempt
            print(f"  Network error ({e}), retrying in {wait}s...", flush=True)
            time.sleep(wait)
    raise ValueError("Max retries exceeded.")

def call_model(api_key, body, retries=6, verbose=False, debug=False):
    """Streaming call. Returns (text, usage, finish_reason)."""
    # Streaming keeps the connection alive during long chain-of-thought responses,
    # preventing timeouts that would occur waiting for a single large response body.
    payload = json.dumps({**body, "stream": True}).encode()

    req = urllib.request.Request(
        API_BASE + "/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        }
    )
    if debug:
        print("--- REQUEST ---")
        print(payload.decode())
        print("---------------")

    for attempt in range(retries):
        try:
            if verbose: print("  connecting...", end=" ", flush=True)
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=30) as resp:
                if verbose: print(f"{resp.status} ({time.time()-t0:.1f}s)", flush=True)
                content = []
                usage = None
                finish = None
                for raw in resp:
                    line = raw.decode().strip()
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = line[len("data:"):].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        delta = json.loads(chunk)
                        if "error" in delta:
                            raise ValueError(f"API error: {delta['error']}")
                        if delta.get("usage"):
                            usage = delta["usage"]
                        choices = delta.get("choices") or []   # final usage chunk has empty choices
                        if choices:
                            content.append(choices[0].get("delta", {}).get("content") or "")
                            finish = choices[0].get("finish_reason") or finish
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Unexpected chunk: {e}") from e
                result = "".join(content)
                if not result.strip():
                    # Seen intermittently (e.g. Qwen via Alibaba); the same request usually works on retry.
                    if attempt < retries - 1:
                        print(f"  Empty response (finish={finish}), retrying...", flush=True)
                        continue
                    raise ValueError("Empty response from model")
                if debug:
                    print("--- RESPONSE ---")
                    print(result)
                    print("----------------")
                return result, usage, finish
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code == 429 or e.code >= 500:
                wait = 2 ** attempt
                print(f"  HTTP {e.code}, retrying in {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise ValueError(f"HTTP {e.code}: {body}")
        except (urllib.error.URLError, TimeoutError) as e:
            wait = 2 ** attempt
            print(f"  Network error ({e}), retrying in {wait}s...", flush=True)
            time.sleep(wait)
    raise ValueError("Max retries exceeded.")

def run_stream(api_key, problems, bodies, args):
    """Yields (index, text, usage, finish_reason, error) in problem order."""
    with ThreadPoolExecutor(max_workers=args.batch_size) as pool:
        for batch_start in range(0, len(problems), args.batch_size):
            idxs = range(batch_start, min(batch_start + args.batch_size, len(problems)))
            futures = [pool.submit(call_model, api_key, bodies[i], verbose=args.verbose, debug=args.debug) for i in idxs]
            for i, future in zip(idxs, futures):
                try:
                    text, usage, finish = future.result()
                    yield i, text, usage, finish, None
                except Exception as e:
                    yield i, "", None, None, str(e)
            if args.delay:
                time.sleep(args.delay)

def run_batch(api_key, problems, bodies, args, run_log):
    """Submits (or resumes) an OpenRouter batch and polls until done.
    Yields (index, text, usage, finish_reason, error); returns the batch-level usage via run_log['batch_usage']."""
    if args.resume:
        batch_id = args.resume
        print(f"Resuming batch {batch_id}")
    else:
        # endpoint/model must be serialized before requests: the API stream-parses the body.
        req = {
            "endpoint": "/v1/chat/completions",
            "model": args.model,
            "requests": [{"custom_id": f"p-{i}", "body": {k: v for k, v in bodies[i].items() if k != "model"}}
                         for i in range(len(problems))],
        }
        if args.debug:
            print("--- BATCH REQUEST (first item) ---")
            print(json.dumps(req["requests"][0], indent=2))
        batch = api_request(api_key, "POST", "/batches", req, timeout=300)
        batch_id = batch["id"]
        print(f"Submitted batch {batch_id}  (resume with --resume {batch_id})")
    run_log["batch_id"] = batch_id

    t0 = time.time()
    last = None
    while True:
        try:
            batch = api_request(api_key, "GET", f"/batches/{batch_id}")
        except ValueError as e:
            # A freshly created batch can 404 for a short while before it becomes visible.
            if str(e).startswith("HTTP 404") and time.time() - t0 < 180:
                time.sleep(args.poll)
                continue
            raise
        status = batch.get("status")
        counts = batch.get("request_counts") or {}
        line = f"  [{time.time()-t0:6.0f}s] {status}  {counts.get('completed', 0)}/{counts.get('total', '?')} done, {counts.get('failed', 0)} failed"
        if line.split("]", 1)[1] != last:
            print(line, flush=True)
            last = line.split("]", 1)[1]
        if status in ("completed", "failed", "expired", "cancelled"):
            break
        time.sleep(args.poll)

    if status != "completed":
        print(f"Batch ended with status {status}: {batch.get('error')}")
    run_log["batch_usage"] = batch.get("usage")

    by_idx = {}
    for r in batch.get("results") or []:
        by_idx[int(r["custom_id"].split("-", 1)[1])] = r
    for i in range(len(problems)):
        r = by_idx.get(i)
        if r is None:
            yield i, "", None, None, f"no result (batch {status})"
            continue
        if r.get("error"):
            yield i, "", None, None, json.dumps(r["error"])
            continue
        body = (r.get("response") or {}).get("body") or {}
        try:
            choice = body["choices"][0]
            text, finish = choice["message"].get("content") or "", choice.get("finish_reason")
        except (KeyError, IndexError):
            text, finish = "", None
        yield i, text, body.get("usage"), finish, None if text.strip() else "Empty response from model"

def usage_cost(usage):
    return (usage or {}).get("cost") or 0.0

def main():
    parser = argparse.ArgumentParser(description="Eval a model on a JSONL dataset via OpenRouter.")
    parser.add_argument("jsonl",              help="Path to .jsonl dataset file")
    parser.add_argument("--model", "-m",      default="openai/gpt-4o-mini", help="OpenRouter model id; a ':batch' suffix implies --batch")
    parser.add_argument("--key",              default="OR_API_KEY", help="Path to API key file (falls back to repo root)")
    parser.add_argument("--limit", "-n",      type=int, default=None, help="Max problems to eval")
    parser.add_argument("--max-tokens",       type=int,   default=1024, help="Max tokens in model response")
    parser.add_argument("--batch-size", "-b",  type=int,   default=1,   help="Parallel requests per batch (streaming mode)")
    parser.add_argument("--delay",            type=float, default=0.0, help="Seconds between batches (streaming mode)")
    parser.add_argument("--batch",            action="store_true", help="Use the OpenRouter Batch API (~50%% price, async)")
    parser.add_argument("--resume",           default=None, help="Resume polling an already-submitted batch id")
    parser.add_argument("--poll",             type=float, default=30.0, help="Seconds between batch status polls")
    parser.add_argument("--out-dir",          default=str(RUNS_DIR), help="Where run logs and usage.jsonl are written")
    parser.add_argument("--verbose", "-v",    action="store_true")
    parser.add_argument("--debug",            action="store_true", help="Print full request and response")
    parser.add_argument("--reasoning-effort", default=None, help="Reasoning effort: xhigh/high/medium/low/minimal/none (o-series, Grok); overrides token-based reasoning")
    parser.add_argument("--reasoning-tokens", type=int, default=None, help="Reasoning max_tokens override (default: max_tokens / 2)")
    parser.add_argument("--no-reasoning",     action="store_true", help="Disable reasoning entirely")
    parser.add_argument("--variant",          default="ordered", choices=list(VARIANT_KEYS),
                        help="Problem presentation: ordered (day order), shuffled (day lines shuffled), "
                             "split (quantity and price as separate shuffled lines)")
    args = parser.parse_args()

    if args.model.endswith(":batch"):
        args.model = args.model[:-len(":batch")]   # batch API takes the plain slug
        args.batch = True
    if args.resume:
        args.batch = True

    api_key = load_api_key(args.key)

    problems = []
    with open(args.jsonl) as f:
        for line in f:
            obj = json.loads(line)
            if "question" in obj:
                problems.append(obj)

    if args.limit:
        problems = problems[:args.limit]

    mode = "batch" if args.batch else "stream"
    print(f"Model      : {args.model}")
    print(f"File       : {args.jsonl}")
    print(f"Probs      : {len(problems)}")
    qkey = VARIANT_KEYS[args.variant]
    missing = sum(1 for p in problems if qkey not in p)
    if missing:
        sys.exit(f"{missing} problems have no '{qkey}' field; regenerate the dataset to get the '{args.variant}' variant")
    print(f"Variant    : {args.variant}")
    print(f"Mode       : {mode}" + ("" if args.batch else f"  (batch size {args.batch_size})"))
    print()

    bodies = [build_body(args.model, p[qkey], args.max_tokens, args.reasoning_effort,
                         args.reasoning_tokens, args.no_reasoning) for p in problems]

    started = datetime.now()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_model = re.sub(r'[^\w.-]', '_', args.model)
    effort_tag = f"_{args.reasoning_effort}" if args.reasoning_effort else ""
    variant_tag = f"_{args.variant}" if args.variant != "ordered" else ""
    base = f"{started:%Y%m%d-%H%M%S}_{safe_model}{effort_tag}_{Path(args.jsonl).stem}{variant_tag}"
    n = 1
    while True:
        log_path = out_dir / (base + (f"-{n}" if n > 1 else "") + ".jsonl")
        try:
            open(log_path, "x").close()   # claim the name atomically so parallel runs never share a log
            break
        except FileExistsError:
            n += 1
    run_log = {}

    correct = 0       # right answer in a requested format (\boxed{} or ####)
    correct_fmt = 0   # right answer, but only found via the fallback
    no_answer = 0
    total = len(problems)
    tokens_in = tokens_out = 0
    summed_cost = 0.0

    results = run_batch(api_key, problems, bodies, args, run_log) if args.batch else run_stream(api_key, problems, bodies, args)

    with open(log_path, "w") as log:
        log.write(json.dumps({"run": {"started": started.isoformat(timespec="seconds"), "model": args.model,
                                      "file": args.jsonl, "mode": mode, "count": total,
                                      "max_tokens": args.max_tokens, "reasoning_effort": args.reasoning_effort,
                                      "reasoning_tokens": args.reasoning_tokens, "no_reasoning": args.no_reasoning,
                                      "variant": args.variant}}) + "\n")
        for i, response, usage, finish, error in results:
            prob = problems[i]
            gold = gold_answer(prob["answer"])
            pred, fmt = extract_answer(response)
            ok   = answers_match(pred, gold)
            fallback = fmt == "fallback"

            if ok and not fallback: correct += 1
            elif ok:                correct_fmt += 1
            elif pred is None:      no_answer += 1

            if ok:                    status = "OK_FMT" if fallback else "OK"
            elif finish == "length":  status = "TRUNC"     # hit max_tokens
            elif error:               status = "ERROR"
            elif pred is None:        status = "NO_ANS"
            else:                     status = "WRONG_FMT" if fallback else "WRONG"
            print(f"[{i+1}/{total}] {status}  gold={gold}  pred={pred}" + (f"  {error}" if error else ""))

            if args.verbose:
                print("  Q:", prob[qkey][:120])
                if not ok:
                    print("  R:", response[-200:])
                print()

            if usage:
                tokens_in  += usage.get("prompt_tokens") or 0
                tokens_out += usage.get("completion_tokens") or 0
                summed_cost += usage_cost(usage)
            log.write(json.dumps({"idx": i, "status": status, "gold": gold, "pred": pred, "fmt": fmt,
                                  "finish_reason": finish, "usage": usage, "error": error, "response": response}) + "\n")

        batch_usage = run_log.get("batch_usage")
        if batch_usage:   # authoritative for batch runs
            tokens_in  = batch_usage.get("prompt_tokens") or tokens_in
            tokens_out = batch_usage.get("completion_tokens") or tokens_out
        cost = usage_cost(batch_usage) if batch_usage else summed_cost

        summary = {"correct": correct, "correct_fmt": correct_fmt, "total": total, "no_answer": no_answer,
                   "prompt_tokens": tokens_in, "completion_tokens": tokens_out, "cost": cost,
                   "batch_id": run_log.get("batch_id")}
        log.write(json.dumps({"summary": summary}) + "\n")

    with open(out_dir / "usage.jsonl", "a") as f:
        f.write(json.dumps({"date": f"{started:%Y-%m-%d}", "time": f"{started:%H:%M:%S}", "model": args.model,
                            "file": args.jsonl, "variant": args.variant, "mode": mode, **summary, "log": log_path.name}) + "\n")

    today_cost = 0.0
    with open(out_dir / "usage.jsonl") as f:
        for line in f:
            row = json.loads(line)
            if row.get("date") == f"{started:%Y-%m-%d}":
                today_cost += row.get("cost") or 0.0

    print()
    print("---")
    print(f"Accuracy  : {correct}/{total}  ({100*correct/total:.1f}%)")
    if correct_fmt:
        print(f"  + format: {correct_fmt} more right, but not in \\boxed{{}} or ####  ({100*(correct+correct_fmt)/total:.1f}% solved)")
    if no_answer:
        print(f"No answer : {no_answer}/{total}")
    print(f"Tokens    : {tokens_in} in / {tokens_out} out")
    print(f"Cost      : ${cost:.4f}   (today: ${today_cost:.4f})")
    print(f"Log       : {log_path}")

if __name__ == "__main__":
    main()
