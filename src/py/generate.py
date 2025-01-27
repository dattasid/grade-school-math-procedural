from gsm2_prob_simple_add import prob_simple_add
from gsm2_prob_simple_add_subtract import prob_simple_add_subtract
from gsm2_prob_simple_buy_price import prob_simple_buy_price
import argparse
import json

# argparse, --N, --clear-lang
parser = argparse.ArgumentParser()
parser.add_argument("--N", type=int, default=5)
parser.add_argument("--easy-read", action="store_true", default=False)
parser.add_argument("--count", type=int, default=10)
parser.add_argument("--dump", action="store_true", default=False)
args = parser.parse_args()

if not args.dump:
  print(json.dumps({"file_metadata":{
    "N": args.N,
    "type": "simple_buy_for_price",
    "easy-read": args.easy_read,
    "count": args.count
  }}))

for i in range(args.count):
  p_json = prob_simple_buy_price(N=args.N, clear_lang=args.easy_read)
  if not args.dump:
    print(json.dumps(p_json))
  else:
    print("Question:\n", p_json["question"], "\nAnswer:\n", p_json["answer"])

