from typing import List
import random
from math import gcd

from lang import num_to_price


def r_chance(rand:random.Random, chance:float):
  return rand.random() < chance

def number_to_words(n:int):
    """Convert a positive integer (up to 99999) to its written form."""
    if n < 0 or n > 9999:
        # raise "Number out of range. Please enter a number between 1 and 999: |"+str(n)+"|"
      return str(n)
    if n==0: return "zero"

    units = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
             "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    words = []

    # Handle thousands
    if n >= 1000:
        words.append(units[n // 1000] + " Thousand")
        n %= 1000

    # Handle hundreds
    if n >= 100:
        words.append(units[n // 100] + " Hundred")
        n %= 100

    # Handle tens and teens
    if 10 <= n < 20:
        words.append(teens[n - 10])
    else:
        if n >= 20:
            words.append(tens[n // 10])
            n %= 10
        # Handle units
        if n > 0:
            words.append(units[n])

    return " ".join(words)

def fraction_to_words(numerator, denominator):
    """Convert a simple fraction (int/int) to its written form."""

    # Handling numerator and denominator
    if numerator == 0:
        return "Zero"
    if denominator == 0:
        return "Undefined (denominator is zero)"
    if numerator % denominator == 0:
        return number_to_words(numerator // denominator)  # It's a whole number

    # For proper fractions
    numerator_words = number_to_words(numerator)
    if denominator < 6:
      denominator_words = {1: "one", 2: "half", 3: "third", 4: "fourth", 5: "fifth"}.get(denominator, "ILLEGAL")
    else:
      denominator_words = number_to_words(denominator) + "th"

    if len(numerator_words.split())>1 or len(denominator_words.split())>1:
      return f"{numerator_words} over {denominator_words}"

    return f"{numerator_words} {denominator_words}"
    # TODO:
    # We always say one half
    # We never say one/three quarters
    # because we dont have rand here

def fraction_simplify(numerator, denominator):
  g = gcd(numerator, denominator)
  return [numerator // g, denominator // g]

def price_to_words_rand(price:int, rand:random.Random):
  vs = num_to_price(price)
  dollar = price // 100
  cent = price % 100
  [dollar_s, cent_s] = vs.split(".")
  strc = [
    lambda d, c: f"\\${vs}",
    lambda d, c: f"{number_to_words(d)} dollars {number_to_words(c)} cents",
    lambda d, c: f"{number_to_words(d)} dollars {cent_s} cents",
    lambda d, c: f"{dollar_s} dollars {cent_s} cents",
  ]
  if cent == 0:
    strc += [
      lambda d, c: f"\\${dollar_s}",
      lambda d, c: f"{dollar_s} dollars",
      lambda d, c: f"{number_to_words(dollar)} dollars",
    ]
  tostr = rand.choice(strc)
  return tostr(dollar, cent)

class NumRel:
  """Abstract class for Number relations"""
  def __init__(self, val:int):
    self.val = val

    self.is_price = False

  def debugStr(self)->str:
    return f"{self.val}"
  def disp_str(self, rand:random.Random, easy:bool=False)->str:
    if not self.is_price:
      if easy:
        return f"{str(self.val)} $item_p"
      tostr = rand.choice([
        lambda n: f"{n} $item_p",
        lambda n: f"{number_to_words(n)} $item_p",
      ])
      return tostr(self.val)  
      
    else:
      if easy:
        return f"\\${num_to_price(self.val)}"
      s = price_to_words_rand(self.val, rand)
      return s

  
  def sol_str(self)->str:
    return str(self.val)
  def adjust_as_price(self, price_mult:int):
    self.val *= price_mult
    self.is_price = True

class NumAddRel(NumRel):
  def __init__(self, delta:int):
    super().__init__(0)
    self.delta = delta

  def debugStr(self)->str:
    return f"+{self.delta}"

  def disp_str(self, rand:random.Random, easy = False)->str:
    if not self.is_price:
      s_val = number_to_words(abs(self.delta)) \
            if r_chance(rand, .5) and not easy\
            else str(abs(self.delta))
      if self.delta > 0:
        return f"{s_val} more $item_p than"
      else:
        return f"{s_val} less $item_p than"
    else:
      s_val = price_to_words_rand(abs(self.delta), rand)
      if easy:
        s_val = "\\$"+num_to_price(abs(self.delta))
      if self.delta > 0:
        return f"{s_val} more than"
      else:
        return f"{s_val} less than"

  def sol_str(self)->str:
    return str(self.delta) if self.delta < 0 else f"+{self.delta}"
  
  def adjust_as_price(self, price_mult:int):
    super().adjust_as_price(price_mult)
    self.delta *= price_mult


MULT_WORDS_MAP = {
  2: ["double", "twice"],
  3: ["triple", "thrice"],
  4: ["quadruple"],
  5: ["quintuple"],
  6: ["hextuple"],
  7: ["septuple"],
}
def mult_word_picker(n:int, rand:random.Random):
  if n not in MULT_WORDS_MAP:
    return f"{n}x"
  return rand.choice(MULT_WORDS_MAP[n])

class NumMulRel(NumRel):
  def __init__(self, n:int, d:int):
    super().__init__(0)
    self.n = n
    self.d = d

  def debugStr(self)->str:
    return f"*{self.n}" if self.d == 1 else f"*{self.n}/{self.d}"

  def disp_str(self, rand:random.Random, easy:bool = False)->str:
    if self.is_price:
      return self.disp_str_price(rand, easy)
    else:
      return self.disp_str_item(rand, easy)

  def disp_str_price(self, rand:random.Random, easy:bool)->str:
    if self.d == 1: # Just multiply
      if (self.n == 1):
        return f"same price as"
      if easy:
        return f"{str(self.n)}x the price$mult_preposition"
      tostr = rand.choice([
        lambda n: f"{n}x the price",
        lambda n: f"{n} times the price",
        lambda n: f"{n} times as much",
        lambda n: f"{number_to_words(n)} times the price",
        lambda n: f"{n*100}% the price",
        lambda n: f"{mult_word_picker(n, rand)} as much",
        lambda n: f"{mult_word_picker(n, rand)} the price",

      ])
      s = tostr(self.n)
    else:
      if easy:
        return f"{self.n}/{self.d} th the price$mult_preposition"
      strc = [
        lambda n, d: f"{n}/{d}th the price",
        lambda n, d: f"{n}/{d}th as much",
        lambda n, d: f"{fraction_to_words(n, d)} the price",
        lambda n, d: f"{fraction_to_words(n, d)} as much",
      ]
      if (100 % self.d) == 0:
        strc += [
          lambda n, d: f"{n*100//d}% the price",
          lambda n, d: f"{number_to_words(n*100//d)} percent the price",
        ]
      tostr = rand.choice(strc)
      s = tostr(self.n, self.d)
    return s+"$mult_preposition"

  def disp_str_item(self, rand:random.Random, easy:bool)->str:
    if self.d == 1: # Just multiply
      if (self.n == 1):
        return f"same number of"
      if easy:
        return f"{str(self.n)}x the $item_p$mult_preposition"
      tostr = rand.choice([
        lambda n: f"{n}x the",
        # lambda n: f"{n} times the",
        lambda n: f"{n} times as many",
        lambda n: f"{number_to_words(n)} times the",
        lambda n: f"{n*100}% of as many",
        lambda n: f"{mult_word_picker(n, rand)} as many",
        lambda n: f"{mult_word_picker(n, rand)} the",

      ])
      s = tostr(self.n)
      return s+" $item_p$mult_preposition"
    else:
      if easy:
        return f"{self.n}/{self.d} th the $item_p$mult_preposition"
      strc = [
        lambda n, d: f"{n}/{d}th the",
        lambda n, d: f"{n}/{d}th as many",
        lambda n, d: f"{fraction_to_words(n, d)} the",
        lambda n, d: f"{fraction_to_words(n, d)} as many",
      ]
      if (100 % self.d) == 0:
        strc += [
          lambda n, d: f"{n*100//d}% the",
          lambda n, d: f"{number_to_words(n*100//d)} percent the",
        ]
      tostr = rand.choice(strc)
      s = tostr(self.n, self.d)
      return s+" $item_p$mult_preposition"
  def sol_str(self)->str:
    return "*"+str(self.n) if self.d == 1 else \
        (f"*{self.n}/{self.d}" if self.n > 1 else f"/{self.d}")



TOTAL_FAKE_IDX = 9999
class NumLine:
  def __init__(self, val:int, idx:int, negative:bool=False):
    self.val = val
    self.known = True

    self.ref:NumLine|None = None # Line to reference
    self.f_n = 1
    self.f_d = 1

    self.index:int = idx # 9999 is total
    self.line_idx:int = -1

    self.rel:NumRel = NumRel(val)

    self.neg = negative
    self.initial_total = False

def find_small_divisors(n:int):
  divs = []
  for i in [2, 3, 4, 5, 6, 10]:
    if n % i == 0:
      divs.append(i)

  return divs

def create_num_series(rand:random.Random, n:int = 3, neg_allowed = False, skip_unknown=False,
                      min_value=1, max_value=50, rel_abs_chance=.1, rel_add_chance=.2):
  """ Create a series of numbers. Also find relationships between them.
    Relationships can be additive or multiplicative.
    For example: a is 30 more than b, or a is 2 times b, or a is 1/2 or 7/12 times b.
    This function will take care of expressing the same relation in different ways.

    This function will add a total which will be last element of the array.

    Args:
      n (int): Number of lines to create. Total is a additional line. But initial amount is included in n as the first line.
      neg_allowed (bool): When on, some numbers can be negative. Also the first number will be the initial total, which can be zero. This is for probalems where a person buys then sells items.
      skip_unknown (bool): Dont create a unknown row, thus calculating relations for all rows. Useful for say unit price list when all prices are known because a quantity is unknown.
  """
  arr:List[NumLine] = []

  uk_idx = rand.randint(0, n-1)
  if skip_unknown:
    uk_idx = -100
  running_tot = -1 # For neg_allowed. running total must always be positive

  # Logic for setting up relations:
  # First row is always absolute
  # Each number at row i will only create relations with earlier rows.
  # This way, it is always possible to find any number from another number.
  # Unknown is excluded, we dont calculate its relations or use it as reference.

  for i in range(n):
    if i == 0:
      val = rand.randint(min_value, max_value)

      line = NumLine(val, i)
      arr.append(line)
      running_tot = val
    else:
      # Which lines we can use as reference? Known lines, and dont use a non zero initial line.
      choices = [line for line in arr[:i] if line.known and line.val > 0]
      ref = None
      if choices:
        ref = rand.choice(choices)
      
      if not ref or r_chance(rand, rel_abs_chance): # small chance of showing absolute anyways
        val = rand.randint(min_value, max_value)
        line = NumLine(val, i)
      else:
        if r_chance(rand, rel_add_chance):
          # small chance of additive relation
          val = rand.randint(min_value, max_value)
          line = NumLine(val, i)
          line.rel = NumAddRel(val - ref.val)
        else:
          # We want the relation to be a ratio of small integers. Find such a small integer
          # as denominator.
          divs = find_small_divisors(ref.val)
          if not divs or (rand.choice([True, False]) and ref.val < 20): #TODO: Adjust the number based on mix/max
            # If we didnt find such a small integer (maybe the number is prime), or
            # if the reference number is small enough, then our value is a multiple.
            mult = rand.choice([2, 3, 4, 5]) # TODO: Dont choose mults that go above max
            val = ref.val * mult
            line = NumLine(val, i)
            line.f_n = mult
            line.f_d = 1
            line.rel = NumMulRel(mult, 1)
          else:
            # Else we are a fraction n/d of the other
            d1 = rand.choice(divs)
            # n1 = rand.randint(1, d1-1)
            n1 = rand.randint(1, 2*d1)
            if n1 >= d1:
              n1 += 1
            [n1, d1] = fraction_simplify(n1, d1)

            val = ref.val * n1 // d1
            line = NumLine(val, i)
            line.f_n = n1
            line.f_d = d1
            line.rel = NumMulRel(n1, d1)

        line.ref = ref


      running_tot += val
    
      arr.append(line)

    if i == uk_idx:
      line.known = False
  
  rand.shuffle(arr)

  line_initial = None
  if neg_allowed:
    running_tot = 0
    # Initial total, 50% chance it is 0
    if r_chance(rand, 0.5):
      val = rand.randint(max_value, max_value) # TODO: Perhaps a separate parameter?
      line_initial = NumLine(val, -1)
      line_initial.initial_total = True

      running_tot += val

    for idx, line in enumerate(arr):

      val = line.val  
      if val < running_tot and r_chance(rand, 0.85):
        line.neg = True
        running_tot -= val
      else:
        line.neg = False
        running_tot += val

  arr = [*arr, NumLine(running_tot, TOTAL_FAKE_IDX)]
  
  for idx, line in enumerate(arr):
    line.line_idx = idx

  if line_initial:
    arr.append(line_initial)

  return arr

def create_num_series_totrel(rand:random.Random, n:int = 3, neg_allowed = False):
  """ Same as above but numbers can be fraction of total"""
  arr:List[NumLine] = []

  uk_idx = rand.randint(0, n-1)
  GOOD_INTS = [3, 4, 5, 6, 7, 10, 20]

  def block1():
    tot_choices = [x for x in GOOD_INTS if x >= n]
    tot = rand.choice(tot_choices)
    arr = []
    remain = tot
    for i in range(n):
      v = rand.randint(1, remain-(n-1-i))
      if i == n-1:
        v = remain
      remain -= v
      arr.append(v)
    # print("**", tot, arr)
    return [tot, arr]
  [tot, frac_arr] = block1()
  mult = rand.randint(2, 20)
  total_line = NumLine(tot * mult, TOTAL_FAKE_IDX)
  for i in range(n):
    val = frac_arr[i] * mult
    line = NumLine(val, i)
    arr.append(line)
    line.ref = total_line
    [n1,d1] = fraction_simplify(frac_arr[i], tot)
    line.rel = NumMulRel(n1, d1)
  
    if r_chance(rand, 0.1):
      line.ref = None
      line.rel = NumRel(line.val)

    if i > 0 and r_chance(rand, 0.4):
      choices = [line for line in arr[:i] if line.known]
      ref = None
      if choices:
        ref = rand.choice(choices)
      
      if not ref:
        pass
      else:
        line.ref = ref
        if r_chance(rand, 0.2):
          line.rel = NumAddRel(line.val - ref.val)
        else:
          [n1, d1] = fraction_simplify(line.val, ref.val)
          line.rel = NumMulRel(n1, d1)
          
    if i == uk_idx:
      line.known = False

  rand.shuffle(arr)
  for idx, line in enumerate(arr):
    line.index = idx

  arr.append(total_line)

  return arr


# arr = create_num_series(n=5)
# arr = create_num_series(n=5, neg_allowed=True)
# arr = create_num_series_totrel(n=3)
# for line in arr:
#   print(
#     "-" if line.neg else "+",
#     line.val, 
#         "v" if line.known else "x",
#         line.ref.index if line.ref else -1, "|| ",
#         line.rel.str()+" "+
#           str(line.ref.val) if line.ref else "??")

# create_num_series_totrel(n=3)