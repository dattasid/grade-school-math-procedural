"""Aggregate eval logs into a CSV and draw the README charts.

  python report.py            # reads runs/{charts_v1,variants_v1,nonce_v1}, writes runs/summary.csv + charts/*.png

Pools every reasoning-effort-high run per (model, steps, variant), across problem sets.
Correct = OK or OK_FMT (right number, any format). Error bars are 95% Wilson intervals.
"""
import csv
import json
import re
from collections import defaultdict
from math import sqrt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RUN_DIRS = ["charts_v1", "variants_v1", "nonce_v1", "acc_v1"]
CHART_DIR = HERE.parent.parent / "charts"
CORRECT = {"OK", "OK_FMT"}

# Panel order: cheapest first.
MODELS = {
    "z-ai/glm-5.3-flash":          "GLM 5.3 Flash",
    "openai/gpt-6-luna":           "GPT-6 Luna",
    "qwen/qwen3.8-flash":          "Qwen 3.8 Flash",
    "google/gemini-3.8-flash":     "Gemini 3.8 Flash",
    "anthropic/claude-haiku-4.5":  "Claude Haiku 4.5",
}

# Reference palette (dataviz skill), light mode; validated: slots 1-2 pass all checks.
SURFACE, INK, INK_2, INK_MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
BLUE, ORANGE = "#2a78d6", "#eb6834"
BOTH_RIGHT, BOTH_WRONG = "#c9c8c1", "#52514e"


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def load_runs():
    """Yields (run header, rows) for complete effort-high logs. Partial logs superseded by a merge are skipped."""
    for d in RUN_DIRS:
        files = sorted((HERE / "runs" / d).glob("*.jsonl"))
        merged = {f.name.replace("_merged", "") for f in files if "_merged" in f.name}
        for f in files:
            if f.name == "usage.jsonl" or f.name in merged or re.search(r"_p46-49|_rerun|_idx\d", f.name):
                continue
            lines = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
            run = lines[0]["run"]
            if run.get("reasoning_effort") != "high":
                continue
            rows = [l for l in lines if "idx" in l]
            summary = next((l["summary"] for l in lines if "summary" in l), {})
            yield f, run, rows, summary


def aggregate():
    agg = defaultdict(lambda: {"k": 0, "n": 0, "cost": 0.0, "tokens_out": 0, "files": []})
    per_problem = {}  # (model, file stem without variant, variant) -> {idx: correct}
    for f, run, rows, summary in load_runs():
        steps = int(re.search(r"data_(\d+)_", Path(run["file"]).name).group(1))
        variant = run.get("variant", "ordered")
        a = agg[(run["model"], steps, variant)]
        a["k"] += sum(r["status"] in CORRECT for r in rows)
        a["n"] += len(rows)
        row_cost = sum((r.get("usage") or {}).get("cost", 0) or 0 for r in rows)
        a["cost"] += row_cost or summary.get("cost") or 0   # batch runs bill per batch, not per row
        a["tokens_out"] += sum((r.get("usage") or {}).get("completion_tokens", 0) or 0 for r in rows)
        a["files"].append(f"{f.parent.name}/{f.name}")
        per_problem[(run["model"], run["file"], variant)] = {r["idx"]: r["status"] in CORRECT for r in rows}
    return agg, per_problem


def write_csv(agg):
    out = HERE / "runs" / "summary.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "steps", "variant", "correct", "total", "accuracy", "ci_low", "ci_high",
                    "cost_per_problem", "tokens_out_per_problem", "logs"])
        for (model, steps, variant), a in sorted(agg.items()):
            lo, hi = wilson(a["k"], a["n"])
            w.writerow([model, steps, variant, a["k"], a["n"], round(a["k"] / a["n"], 4), round(lo, 4), round(hi, 4),
                        round(a["cost"] / a["n"], 5), round(a["tokens_out"] / a["n"]), " ".join(a["files"])])
    return out


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK_MUTED)
    ax.tick_params(colors=INK_2, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def chart_accuracy(agg):
    fig, axes = plt.subplots(1, len(MODELS), figsize=(14, 3.9), sharey=True, facecolor=SURFACE)
    xticks = [10, 30, 50, 100, 200]
    for ax, (model, label) in zip(axes, MODELS.items()):
        style_axes(ax)
        pts = sorted((s, a) for (m, s, v), a in agg.items() if m == model and v == "ordered")
        xs = [s for s, _ in pts]
        ys = [100 * a["k"] / a["n"] for _, a in pts]
        cis = [wilson(a["k"], a["n"]) for _, a in pts]
        lo = [y - 100 * c[0] for y, c in zip(ys, cis)]
        hi = [100 * c[1] - y for y, c in zip(ys, cis)]
        ax.plot(xs, ys, color=BLUE, linewidth=2, zorder=2)
        ax.errorbar(xs, ys, yerr=[lo, hi], fmt="none", ecolor=BLUE, elinewidth=1.2, capsize=3, alpha=0.55, zorder=2)
        ax.scatter(xs, ys, s=42, color=BLUE, edgecolor=SURFACE, linewidth=2, zorder=3)
        for (s, a), y in zip(pts, ys):
            ax.annotate(f"{a['k']}/{a['n']}", (s, y), xytext=(0, 9), textcoords="offset points", ha="center",
                        fontsize=8, color=INK_2, zorder=4,
                        bbox=dict(boxstyle="square,pad=0.15", facecolor=SURFACE, edgecolor="none"))
        a50 = agg.get((model, 50, "ordered"))
        cost = f"${a50['cost'] / a50['n']:.3f} per 50-step problem" if a50 else ""
        ax.set_title(f"{label}\n", fontsize=11, color=INK, loc="left", fontweight="bold")
        ax.text(0, 1.02, cost, transform=ax.transAxes, fontsize=8.5, color=INK_2)
        ax.set_xscale("log")
        ax.set_xticks(xticks, [str(x) for x in xticks])
        ax.minorticks_off()
        ax.set_xlim(8, 260)
        ax.set_ylim(0, 112)
        ax.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
        ax.set_xlabel("steps (days of purchases)", fontsize=9, color=INK_2)
    fig.suptitle("Accuracy vs. problem length", x=0.01, ha="left", fontsize=14, color=INK, fontweight="bold")
    fig.text(0.01, 0.885, "Reasoning effort high · labels = correct/attempted · bars = 95% Wilson interval · "
             "pooled across problem sets", fontsize=9, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=2.5)
    out = CHART_DIR / "accuracy_vs_steps.png"
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return out


def chart_nonce(per_problem):
    rows = []
    for model, label in MODELS.items():
        real = next((v for (m, f, var), v in per_problem.items() if m == model and var == "ordered" and "data_50_60" in f), None)
        nonce = next((v for (m, f, var), v in per_problem.items() if m == model and var == "ordered_nonce" and "data_50_60" in f), None)
        if not real or not nonce:
            continue
        common = sorted(set(real) & set(nonce))
        both = sum(real[i] and nonce[i] for i in common)
        only_r = sum(real[i] and not nonce[i] for i in common)
        only_n = sum(nonce[i] and not real[i] for i in common)
        rows.append((label, both, only_r, only_n, len(common) - both - only_r - only_n, len(common),
                     sum(real[i] for i in common), sum(nonce[i] for i in common)))
    if not rows:
        return None
    fig, ax = plt.subplots(figsize=(10, 1.2 + 0.9 * len(rows)), facecolor=SURFACE)
    style_axes(ax)
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    segs = [("both right", BOTH_RIGHT, INK), ("right only with real words", BLUE, "white"),
            ("right only with made-up words", ORANGE, "white"), ("both wrong", BOTH_WRONG, "white")]
    for y, r in enumerate(rows):
        left = 0
        for j, (name, color, txt) in enumerate(segs):
            w = r[1 + j]
            ax.barh(y, w, left=left, height=0.55, color=color, edgecolor=SURFACE, linewidth=2,
                    label=name if y == 0 else None)
            if w >= 2:
                ax.text(left + w / 2, y, str(w), ha="center", va="center", fontsize=9, color=txt)
            left += w
        ax.text(left + 0.6, y, f"real {r[6]}/{r[5]} · made-up {r[7]}/{r[5]}", va="center", fontsize=9, color=INK_2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=10, color=INK)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_xlim(0, rows[0][5] + 14)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.02), ncol=4, frameon=False, fontsize=9, labelcolor=INK_2,
              handlelength=1, handleheight=1)
    fig.suptitle("Real names vs. made-up words: same 50 problems, same numbers", x=0.01, ha="left",
                 fontsize=13, color=INK, fontweight="bold")
    fig.text(0.01, 0.84 if len(rows) < 3 else 0.88,
             "Names, items and day labels swapped for nonce words (\"Pukad bought 21 gebazs on Tatin\"). "
             "Flips go both ways about equally: no contamination effect.", fontsize=9, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.82))
    out = CHART_DIR / "nonce_flips.png"
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return out


def chart_cost_accuracy():
    """One color per model, one point per problem length; all models on the same first 10 problems (charts_v1)."""
    # Validated --pairs all: passes; aqua/red sits in the CVD 6-8 band, so shapes + direct labels are required.
    style = {
        "z-ai/glm-5.3-flash":         ("#2a78d6", "o"),
        "openai/gpt-6-luna":          ("#4a3aa7", "s"),
        "qwen/qwen3.8-flash":         ("#1baf7a", "^"),
        "google/gemini-3.8-flash":    ("#eda100", "D"),
        "anthropic/claude-haiku-4.5": ("#e34948", "v"),
    }
    pts = defaultdict(list)
    for f, run, rows, summary in load_runs():
        steps = int(re.search(r"data_(\d+)_", Path(run["file"]).name).group(1))
        if f.parent.name != "charts_v1" or steps not in (10, 30, 50) or run["model"] not in style:
            continue
        cost = sum((r.get("usage") or {}).get("cost", 0) or 0 for r in rows) or summary.get("cost") or 0
        k = sum(r["status"] in CORRECT for r in rows)
        pts[run["model"]].append((steps, cost / len(rows), 100 * k / len(rows), run.get("mode")))

    fig, ax = plt.subplots(figsize=(10, 5.6), facecolor=SURFACE)
    style_axes(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    sizes = {10: 40, 30: 85, 50: 150}
    for model, label in MODELS.items():
        color, marker = style[model]
        p = sorted(pts[model])
        xs, ys = [c for _, c, _, _ in p], [a for _, _, a, _ in p]
        ax.plot(xs, ys, color=color, linewidth=1.5, alpha=0.6, zorder=2)
        ax.scatter(xs, ys, s=[sizes[s] for s, *_ in p], color=color, marker=marker, edgecolor=SURFACE,
                   linewidth=2, zorder=3, label=label)
        batch = " (batch price)" if p[-1][3] == "batch" else ""
        # (point index to label, offset, alignment): placed by hand to avoid collisions
        at, off, ha = {"qwen/qwen3.8-flash": (1, (10, -4), "left"),
                       "google/gemini-3.8-flash": (2, (0, 12), "right"),
                       "anthropic/claude-haiku-4.5": (2, (0, -24), "center")}.get(model, (-1, (10, 8), "left"))
        ax.annotate(label + batch, (xs[at], ys[at]), xytext=off, textcoords="offset points",
                    ha=ha, fontsize=9, color=INK, zorder=4)
    ax.set_xscale("log")
    ax.set_xlim(2e-4, 0.6)
    ticks = [0.001, 0.01, 0.1]
    ax.set_xticks(ticks, ["$0.001", "$0.01", "$0.10"])
    ax.minorticks_off()
    ax.set_ylim(50, 108)
    ax.set_yticks([50, 60, 70, 80, 90, 100], [f"{v}%" for v in (50, 60, 70, 80, 90, 100)])
    ax.set_xlabel("cost per problem (log scale)", fontsize=9, color=INK_2)
    ax.set_ylabel("accuracy", fontsize=9, color=INK_2)
    leg = ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK_2, markerscale=0.8)
    for h in leg.legend_handles:
        h.set_sizes([50])
    ax.text(0.99, 0.30, "marker size: 10 · 30 · 50 steps", transform=ax.transAxes, ha="right",
            fontsize=8.5, color=INK_2)
    fig.suptitle("Cost vs. accuracy: same 10 problems at 10, 30 and 50 steps", x=0.01, ha="left",
                 fontsize=13, color=INK, fontweight="bold")
    fig.text(0.01, 0.905, "Reasoning effort high · each point = 10 problems, so ±1 problem = ±10 points · "
             "cost as billed (batch runs ~50% off)", fontsize=9, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    out = CHART_DIR / "cost_vs_accuracy.png"
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return out


def chart_glm_luna():
    """GLM vs Luna on the data_v4 sets only: 50 problems per point, identical problems for both models."""
    series = {"z-ai/glm-5.3-flash": (BLUE, "o"), "openai/gpt-6-luna": (ORANGE, "s")}
    pts = defaultdict(dict)
    for f, run, rows, summary in load_runs():
        name = Path(run["file"]).name
        m = re.fullmatch(r"data_(\d+)_(?:50|60)\.jsonl", name)
        if not m or "data_v4" not in run["file"] or run.get("variant", "ordered") != "ordered" or run["model"] not in series:
            continue
        rows = [r for r in rows if r["idx"] < 50]
        pts[run["model"]][int(m.group(1))] = (sum(r["status"] in CORRECT for r in rows), len(rows))

    fig, ax = plt.subplots(figsize=(9, 5.2), facecolor=SURFACE)
    style_axes(ax)
    for j, (model, (color, marker)) in enumerate(series.items()):
        steps = sorted(pts[model])
        ks = [pts[model][s] for s in steps]
        ys = [100 * k / n for k, n in ks]
        cis = [wilson(k, n) for k, n in ks]
        xs = [s + (j - 0.5) * 0.8 for s in steps]   # small dodge so the error bars don't overlap
        ax.errorbar(xs, ys, yerr=[[y - 100 * c[0] for y, c in zip(ys, cis)], [100 * c[1] - y for y, c in zip(ys, cis)]],
                    fmt="none", ecolor=color, elinewidth=1.2, capsize=3, alpha=0.5, zorder=2)
        ax.plot(xs, ys, color=color, linewidth=2, zorder=2)
        ax.scatter(xs, ys, s=60, color=color, marker=marker, edgecolor=SURFACE, linewidth=2, zorder=3, label=MODELS[model])
        for x, y, (k, n) in zip(xs, ys, ks):
            ax.annotate(f"{k}/{n}", (x, y), xytext=(14 if j else -14, -3), textcoords="offset points",
                        ha="left" if j else "right", fontsize=8.5, color=INK_2)
        ax.annotate(MODELS[model], (xs[-1], ys[-1]), xytext=(10, 10 if j else -16), textcoords="offset points",
                    fontsize=10, color=INK, fontweight="bold")
    ax.set_xticks([10, 20, 30, 40, 50])
    ax.set_xlim(5, 58)
    ax.set_ylim(50, 102)
    ax.set_yticks([50, 60, 70, 80, 90, 100], [f"{v}%" for v in (50, 60, 70, 80, 90, 100)])
    ax.set_xlabel("steps (days of purchases)", fontsize=9, color=INK_2)
    ax.legend(loc="lower left", frameon=False, fontsize=9, labelcolor=INK_2)
    fig.suptitle("GLM 5.3 Flash vs. GPT-6 Luna: accuracy vs. problem length", x=0.01, ha="left",
                 fontsize=13, color=INK, fontweight="bold")
    fig.text(0.01, 0.9, "Same 50 problems per length for both models · reasoning effort high · "
             "bars = 95% Wilson interval · both ~$0.003 per 50-step problem", fontsize=9, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    out = CHART_DIR / "glm_vs_luna.png"
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return out, dict(pts)


def main():
    CHART_DIR.mkdir(exist_ok=True)
    agg, per_problem = aggregate()
    print("wrote", write_csv(agg))
    print("wrote", chart_accuracy(agg))
    print("wrote", chart_nonce(per_problem))
    print("wrote", chart_cost_accuracy())
    out, pts = chart_glm_luna()
    print("wrote", out, pts)


if __name__ == "__main__":
    main()
