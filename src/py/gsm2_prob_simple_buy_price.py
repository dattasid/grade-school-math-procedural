from gsm2 import create_num_series, price_to_words_rand, r_chance, NumLine
from itemdb import getItemList, getOneItem, pickItemGroup, ItemDB_reset, ItemDB_getTimeSeries, ITEMDB
from random import Random
from typing import List, Dict, cast
from lang import FEMALE_NAMES, MALE_NAMES, VERBS_HT, replace_variables, getPlural, \
  join_with_and, replace_name_with_pronoun, num_to_price, cleanup_str, ShuffledList

rand = Random()

# TODO
#  Subset total
#  confuse lines
# Initial should have relation
# Initial could be the uknown
def prob_simple_buy_price(N=3,
  force_no_neg=False,
  force_q_at_end=False,
  force_no_shuffle=False,
  clear_lang=False):
  """ Generates problems of the form:
      Person buys A amount of item for price B on day <Day>.
        This is repeated N number of times.
      Total is T.
      The total is unknown, or the amount or price is unknown.
      Amounts and prices will often given in relation to the same from another day.
      At least one amount and price must be absolute number.
      The relations are given in such a way that all amounts can be derived. Algebra (declaring x) is not needed.
  """

  if N > 12:
    raise ValueError("N must be less than <= 12 for now.")
    #TODO: Implement Time series that is Days of Month eg 1 Jan, 2 Jan etc

  ST_INITIAL = ShuffledList(rand,
          "$name had \\$$m_count in the start.",
          "$name started with \\$$m_count.",
        )
  ST_BASE = ShuffledList(rand,
    "$name $verb_past $quantity_clause on $time for $price_clause each.",
    "$name $verb_past $quantity_clause for $price_clause per item on $time.",
    "$name paid $price_clause each on $time for $quantity_clause.",
    "$name paid $price_clause per item for $quantity_clause on $time.",

    "On $time, $name $verb_past $quantity_clause for $price_clause each.",
    "On $time, $name paid $price_clause per item for $quantity_clause.",

    "$name $verb_past $quantity_clause on $time. $name paid $price_clause each."
    "$name paid $price_clause per item on $time. $name $verb_past $quantity_clause."
  )
  ST_BASE_CLEAR = ShuffledList(rand,
    "On $time, $name $verb_past $quantity_clause. On $time, $name paid $price_clause per $item_s.",
  )
  # He bought thrice as many apples on Monday as [he bought] on Tuesday, for twice the price he paid on Wednesday.
  # ST_REL_T  = "$name $verb_past $quantity_clause for $price_clause"
  # ...3 apples on Monday...
  ST_Q_CLAUSE_ABS = "$rel_str"
  # ...3x the apples on Monday as Tuesday
  ST_Q_CLAUSE_REL = "$rel_str $target_time"

  # ...3 dollars...
  ST_P_CLAUSE_ABS = "$price_rel_str"
  # ...3x the apples on Monday as Tuesday
  ST_P_CLAUSE_REL = "$price_rel_str $target_time"

  ST_BASE_QUANTITY = "On $time, $name $verb_past $quantity_clause."
  ST_BASE_PRICE = "On $time, $name paid $price_clause per item." # Note we can change item to $item_s

  ST_TOT    = "$name spent a total of $total_value."

  ST_Q_TOTAL = ShuffledList(rand,
    "How much did $name spend in total?",
    "What was the total amount $name spent?",
    "How much money did $name spend altogether?",
    "What is the sum of $name's expenditures?",
    "What is the total cost incurred by $name?",
    "How much did $name's total expenses amount to?"
  )
  ST_Q_QUANTITY = ShuffledList(rand,
    "How many $item_p did $name buy on $time?",
    "What quantity of $item_p did $name purchase on $time?",
    "How much of $item_p did $name acquire on $time?",
    "On $time, how many $item_p were bought by $name?",
    "How many $item_p did $name get on $time?",
    "What was the number of $item_p that $name bought on $time?"
  )
  ST_Q_PRICE = ShuffledList(rand,
    "How much did $name spend per $item_s on $time?",
    "What was the total amount $name spent per $item_s on $time?",
    "How much money did $name allocate to each $item_s on $time?",
    "What did $name spend per $item_s for $time?",
    "Can you tell me the amount $name spent on each $item_s on $time?",
    "How much did $name pay per $item_s throughout $time?"
  )
  # He bought thrice as many apples as bananas, for twice the price he paid on Wednesday.

  ST_PRE_SHORT = "$name $verb_past "
  ST_BASE_SHORT = "$rel_str"
  ST_REL_SHORT  = "$rel_str on $time as $target_time"
  ST_UKNOWN_SHORT = rand.choice(["a few $item_p", "some $item_p"])

  ST_SOL_Q_BASE = "$verb_past_p on $time: $count"
  ST_SOL_P_BASE = "Price on $time: $count"
  ST_SOL_Q_REL =  "Quantity on $time: $target_time$mult = $target_count$mult = $count"
  ST_SOL_P_REL =  "Price on $time: $target_time$mult = $target_count$mult = $count"

  ST_SOL_Q_BASE_S = "Q_$time = $count"
  ST_SOL_P_BASE_S = "P_$time = $count"
  ST_SOL_Q_REL_S =  "Q_$time = Q_$target_time$mult = $target_count$mult = $count"
  ST_SOL_P_REL_S =  "P_$time = P_$target_time$mult = $target_count$mult = $count"



  ST_SOL_MUL = "Spent on $time: $q_count * $p_count = $count"

  ST_SOL_KNOWN_INITIAL = "Initial: $count"
  ST_SOL_KNOWN_TOT = "Final total: $count"


  ST_SOL_TOT = "Total: $line_count_join = \\$$count\n#### $count"
  ST_SOL_ITEM = "Total except $time: $line_count_join = \\$$known_count"
  ST_SOL_ITEM_PLUS = "Spent on $time: \\$$total_count - \\$$known_count = \\$$count"
  # ST_SOL_ITEM_MINUS = "$verb_past_p on $time: $known_count-$total_count = $item_count\n#### $item_count"
  ST_SOL_ITEM_Q = "Quantity on $time: $amount / \\$$price = $count\n#### $count"
  ST_SOL_ITEM_P = "Price on $time: $amount / $count = \\$$price\n#### $price"

  ST_RESTATE_PREFIX = "Let us think step by step.\nIn this problem we see there the person buying only one type of item. " \
                  "The quantity and price varies over time. Let us denote this by Q_day and P_day.\n" \
                  "Let us rewrite the problem in a simpler manner."
  

  unknown_type = rand.choice(["quantity", "quantity", "price", "price", "total"])
  quantities = create_num_series(rand, n=N,
                           neg_allowed=False, # Debug
                           skip_unknown=(unknown_type != "quantity"),
                           )
  price_resolution = rand.choice([1, 2, 4]) # 1=int, 2=.5, 4=.25
  price_mult = 100 // price_resolution
  prices = create_num_series(rand, n=N, neg_allowed=False, skip_unknown=(unknown_type != "price"),
                             min_value = 2*price_resolution, max_value = 8*price_resolution,
                             rel_add_chance=0.0)
  for p in prices:
    p.val *= price_mult
    p.rel.adjust_as_price(price_mult)

  activity_type = rand.choice([
    {"verb":["buy", "sell"], "cats":["food", "stationary"]},
    {"verb":["buy", "eat"], "cats":["food"]}
  ])

  ItemDB_reset(rand)
  itemgrp = pickItemGroup(rand, cast(List, activity_type["cats"]))
  verb_plus = VERBS_HT[activity_type["verb"][0]] # type: ignore
  verb_minus = VERBS_HT[activity_type["verb"][1]] # type: ignore
  item = itemgrp.work_items[0]

  time_series = ItemDB_getTimeSeries(rand, N=N).work_items[:N]
  if "food" in itemgrp.categories and N <= 7:
    time_series = ITEMDB["time_wod"].work_items[:N]

  if r_chance(rand, 0.5):
    name = rand.choice(MALE_NAMES)
    pronoun = "He"
  else:
    name = rand.choice(FEMALE_NAMES)
    pronoun = "She"
  pronoun_l = pronoun.lower()

  if r_chance(rand, 0.1):
    pronoun = "They"

  vars = {
    "name": name,

    "item_s": item,
    "item_p": getPlural(item),
    "group_item_p": itemgrp.grp,

    "mult_preposition": " as",
    "verb_diff": ""

  }
  q_lines:List[str] = []
  q_lines_short:List[str] = []

  line_initial = None
  if quantities[-1].initial_total:
    line_initial = quantities.pop()
    vars_1 = {**vars, "rel_str": line_initial.rel.disp_str(rand, easy=clear_lang)}
    s = replace_variables(ST_INITIAL, vars_1) # type: ignore
    s = replace_variables(s, vars_1) # type: ignore
    q_lines.append(s)

  if True:
    for idx, price in enumerate(quantities):
      # print("--", line.neg,
      #       line.val, line.ref.line_idx if line.ref else "-9999",
      #       line.rel.disp_str(rand))
      pr = prices[idx]
      # print(f"**** {price.neg} {price.val} {num_to_price(prices[idx].val)} {price.rel.disp_str(rand)}*{price.ref.val if price.ref else -11} {pr.rel.disp_str(rand)}*{pr.ref.val if pr.ref else -11}")

  # print(time_series) #debug
  quantities = quantities[:-1]# without total
  prices = prices[:-1] # without total

  question_lines:List[str] = []
  restate_lines:List[str] = []
  solution_lines:List[str] = []

  total_spent = 0
  known_spent = 0
  unknown_amt = None
  for idx, quantity in enumerate(quantities):
    the_price = prices[idx]

    total_spent += quantity.val * the_price.val
    if quantity.known and the_price.known:
      known_spent += quantity.val * the_price.val
    vars_1 = {**vars,
          "verb_base": verb_plus.base,
          "verb_past": verb_plus.past,
          "verb_past_p": verb_plus.past_p,
        }
    vars_1["count"] = str(quantity.val)
    vars_1["rel_str"] = quantity.rel.disp_str(rand, easy=clear_lang)
    vars_1["time"] = time_series[idx]
    vars_1["price_rel_str"] = prices[idx].rel.disp_str(rand, easy=clear_lang)

    # print(prices[idx].rel.is_price, prices[idx].rel.disp_str(rand))
    # print(line.ref, line.ref.line_idx if line.ref else -999)
    # print(quantity.val, the_price.val, quantity.known, the_price.known)
    
    if not quantity.ref:
      quantity_clause = replace_variables(ST_Q_CLAUSE_ABS, vars_1)
      quantity_clause = replace_variables(quantity_clause, vars_1)
    else:
      vars_1["target_time"] = time_series[quantity.ref.line_idx]
      quantity_clause = replace_variables(ST_Q_CLAUSE_REL, vars_1)
      quantity_clause = replace_variables(quantity_clause, vars_1)
    
    if not the_price.ref:
      price_clause = replace_variables(ST_P_CLAUSE_ABS, vars_1)
      # price_clause = replace_variables(price_clause, vars_1)
    else:
      vars_1["target_time"] = time_series[the_price.ref.line_idx]
      price_clause = replace_variables(ST_P_CLAUSE_REL, vars_1)
      # price_clause = replace_variables(price_clause, vars_1)

    vars_1["quantity_clause"] = quantity_clause
    vars_1["price_clause"] = price_clause

    if quantity.known and the_price.known:
      base_template = ST_BASE if not clear_lang else ST_BASE_CLEAR
      s = replace_variables(base_template.next(), vars_1)
      s = replace_variables(s, vars_1)
    elif quantity.known:
      s = replace_variables(ST_BASE_QUANTITY, vars_1)
      s = replace_variables(s, vars_1)
    elif the_price.known:
      s = replace_variables(ST_BASE_PRICE, vars_1)
      s = replace_variables(s, vars_1)
    else:
      raise Exception("Illegal condition: quantity and price unknown")

    if not quantity.known:
      unknown_amt = quantity
    elif not the_price.known:
      unknown_amt = the_price

    # print("++", price_clause, the_price.rel.is_price)
    # print("--", cleanup_str(s))
    s = cleanup_str(s)
    question_lines.append(s)

  if unknown_type != "total":
    vars_1 = {**vars,
      "total_value": price_to_words_rand(total_spent, rand),
    }
    s = replace_variables(ST_TOT, vars_1)
    s = replace_variables(s, vars_1)
    s = cleanup_str(s)
    # print("--", s)
    question_lines.append(s)

  # -------- Ask Question
  if unknown_type == "total":
    s = replace_variables(ST_Q_TOTAL.next(), vars)
  elif not unknown_amt:
    raise Exception("No Unknown p/q")
  else:
    vars["time"] = time_series[unknown_amt.line_idx]
    if unknown_type == "quantity":
      s = replace_variables(ST_Q_QUANTITY.next(), vars)
      # print("How many $item_p did $name buy on ?"+time_series[unknown_amt.line_idx])
    elif unknown_type == "price":
      s = replace_variables(ST_Q_PRICE.next(), vars)
      # print("How much did $name spend per $item_s on ?"+time_series[unknown_amt.line_idx])
    else:
      raise Exception("Unknown unknown_type "+unknown_type)
  s = replace_variables(s, vars)

  s = cleanup_str(s)
  question_lines.append(s)
  # print(s)

  # -----Solution
  vars["verb_past_p"] = verb_plus.past_p.capitalize()
  if True:
    # Restate problem in a simple manner
    restate_lines.append(ST_RESTATE_PREFIX) # TODO actaully add after shuffle

    # NOTE: If we shuffle problem statements we need to shuffle restate statements too
    # so they are always in same order
    for idx in range(N):
      quantity = quantities[idx]
      price = prices[idx]
      time = time_series[idx]
      sq = ""
      sp = ""
      if quantity.known:
        if quantity.ref:
          target_time = time_series[quantity.ref.line_idx]
          sq = f"Q_{time} = Q_{target_time}{quantity.rel.sol_str()}"
        else:
          sq = f"Q_{time} = {quantity.rel.sol_str()}"
        sq += ". "

      if price.known:
        if price.ref:
          target_time = time_series[price.ref.line_idx]
          sp = f"P_{time} = P_{target_time}{price.rel.sol_str()}"
        else:
          sp = f"P_{time} = {price.rel.sol_str()}"
        sp += "."

      restate_lines.append(sq+sp)
    # print("\n".join(restate_lines))


    exact_known_q = set()
    exact_known_p = set()

    for idx, line in enumerate(quantities):
      if line.known and not line.ref:
        exact_known_q.add(line.line_idx)
        s = replace_variables(ST_SOL_Q_BASE_S, {**vars, 
                "time": time_series[line.line_idx],
                "count": str(line.val)})
        s = cleanup_str(s)
        solution_lines.append(s)
        # print(s)

    # ---------- QUANTITIES
    while True:
      new_this_time = 0
      # print ("!!!", len(exact_known_q), N)
      for idx, line in enumerate(quantities):
        if line.known and line.line_idx not in exact_known_q \
             and line.ref and line.ref.line_idx in exact_known_q:

          exact_known_q.add(line.line_idx)
          new_this_time += 1
          s = replace_variables(ST_SOL_Q_REL_S, {**vars, 
                "time": time_series[line.line_idx],
                "count": str(line.val),
                
                "target_time": time_series[line.ref.line_idx],
                "target_count": str(line.ref.val),
                "mult": line.rel.sol_str()})
          s = cleanup_str(s)
          solution_lines.append(s)
          # print(s)
      if new_this_time == 0:
        break

    # ---------- PRICES
    for idx, price in enumerate(prices):
      if price.known and not price.ref:
        exact_known_p.add(price.line_idx)
        s = replace_variables(ST_SOL_P_BASE_S, {**vars, 
                "time": time_series[price.line_idx],
                "count": num_to_price(price.val)})
        s = cleanup_str(s)
        solution_lines.append(s)
        # print(s)
    while True:
      new_this_time = 0
      # print ("!!!", len(exact_known_p), N)
      for idx, price in enumerate(prices):
        if price.known and price.line_idx not in exact_known_p \
             and price.ref and price.ref.line_idx in exact_known_p:

          exact_known_p.add(price.line_idx)
          new_this_time += 1
          s = replace_variables(ST_SOL_P_REL_S, {**vars, 
                "time": time_series[price.line_idx],
                "count": num_to_price(price.val),
                
                "target_time": time_series[price.ref.line_idx],
                "target_count": num_to_price(price.ref.val),
                "mult": price.rel.sol_str()})
          s = cleanup_str(s)
          solution_lines.append(s)
          # print(s)
      if new_this_time == 0:
        break

    # ---------- TOTALS
    if True:
      line_counts:List[str] = []
      for i in range(N):
        if not quantities[i].known or not prices[i].known:
          continue
        mult_count = num_to_price(quantities[i].val * prices[i].val)
        s = replace_variables(ST_SOL_MUL, {**vars,
                "time": time_series[i],
                "q_count": str(quantities[i].val),
                "p_count": "$"+num_to_price(prices[i].val),
                "count": "$"+mult_count,
        })
        line_counts.append("$"+mult_count)

        solution_lines.append(s)
        # print(s)
    
      # --------- Actual solution
      line_count_join = " + ".join(line_counts)
      if unknown_type == "total":
        s = replace_variables(ST_SOL_TOT, {**vars, 
                  "count": num_to_price(total_spent),
                  "line_count_join": line_count_join})
        s = cleanup_str(s)
        solution_lines.append(s)
        # print(s)
      else:
        if not unknown_amt:
          raise Exception("No Unknown p/q")
        vars["time"] = time_series[unknown_amt.line_idx]
        s = replace_variables(ST_SOL_ITEM, {**vars, 
                  "known_count": num_to_price(total_spent),
                  "line_count_join": line_count_join})
        s = cleanup_str(s)
        solution_lines.append(s)
        # print(s)

        time_amount = quantities[unknown_amt.line_idx].val * prices[unknown_amt.line_idx].val
        s = replace_variables(ST_SOL_ITEM_PLUS, {**vars, 
                  "total_count": num_to_price(total_spent),
                  "known_count": num_to_price(known_spent),
                  "count": num_to_price(time_amount)})
        s = cleanup_str(s)
        solution_lines.append(s)
        # print(s)

        if unknown_type == "quantity":
          s = replace_variables(ST_SOL_ITEM_Q, {**vars,
              "amount": num_to_price(time_amount),
              "price": num_to_price(prices[unknown_amt.line_idx].val),
              "count": str(quantities[unknown_amt.line_idx].val)
          })
        elif unknown_type == "price":
          s = replace_variables(ST_SOL_ITEM_P, {**vars,
              "amount": num_to_price(time_amount),
              "price": num_to_price(prices[unknown_amt.line_idx].val),
              "count": str(quantities[unknown_amt.line_idx].val)
          })
        s = cleanup_str(s)
        solution_lines.append(s)
        # print(s)

  return {"question": "\n".join(question_lines),
         "answer": "\n".join(restate_lines + solution_lines)}
