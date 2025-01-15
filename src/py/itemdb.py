from random import Random
from typing import List, Dict

ITEMS = [
    {
    "id": "food_pizza",
    "category": ["food"],
    "group_name": "pizzas",
    "items": [
      "Margherita Pizza", "Pepperoni Pizza", "BBQ Chicken Pizza", "Hawaiian Pizza", "Veggie Pizza", "Meat Lovers Pizza", "Buffalo Chicken Pizza", "Supreme Pizza", "Cheese Pizza", "Mushroom Pizza"
      ]
  },
  {
    "id": "stationary_gen",
    "category": ["stationary"],
    "group_name": "stationary items",
    "items": ["notebook", "pen", "pencil", "eraser", "ruler", "highlighter", "marker", "scissor", "glue stick", "stapler", "paper clip", "binder clip", "folder", "sticky note", "correction tape", "sharpener", "compass", "protractor", "calendar", "index card"]
  },
  {
    "id": "stationary_books",
    "category": ["stationary"],
    "group_name": "books",
    "items": ["textbook", "e-book", "novel", "reference guide", "dictionary", "comic", "magazine", "journal", "workbook", "encyclopedia"],
  },
  {
    "id": "stationary_clothes",
    "category": ["stationary"],
    "group_name": "clothes",
    "items": ["uniform", "t-shirt", "jeans", "jacket", "hoodie", "hat", "socks", "shoes", "scarf"],
  },
  {
    "id": "stationary_art",
    "category": ["stationary"],
    "group_name": "art supplies",
    "items": ["paint", "brush", "sketchbook", "canvas", "palette", "pencil crayon", "charcoal stick", "marker", "eraser", "stencil"],
  },
  {
    "id": "stationary_sports",
    "category": ["stationary"],
    "group_name": "sports items",
    "items": ["ball", "racket", "bat", "glove", "helmet", "net", "yoga mat", "jump rope", "weights", "goal post"],
  },
]

def getOneItem(rng:Random):
  type = rng.choice(ITEMS)
  return rng.choice(type["items"])

def getItemList(rng:Random, count:int):
  type = rng.choice(ITEMS)
  items = type["items"]

  if len(items) < count:
    return ["ERROR"]
  return items[:count]

def pickItemGroup(rng:Random, allowed_cat:List[str]):
  opts:List[ItemSet] = []
  s_cats = set(allowed_cat)
  for r in ITEMDB.values():
    if bool(set(r.categories) & s_cats):
      opts.append(r)

  return rng.choice(opts)

ITEMDB:Dict[str, "ItemSet"] = {}
class ItemSet:
  """Shuffles on init, provides items one by one"""
  def __init__(self, id:str, categories:List[str], items:List[str]=[]):
    self.id = id
    self.grp = ""
    self.categories = categories
    self.items = items
    
    self.work_items = []
    self.idx = -1

    ITEMDB[id] = self

  def begin(self, rng:Random):
    self.idx = -1
    self.work_items = self.items[:]
    rng.shuffle(self.work_items)

  def getItem(self):
    self.idx += 1
    return self.work_items[self.idx]
  
class ItemsWOD(ItemSet):
  def __init__(self):
    super().__init__("time_wod", ["time"])
    self.items = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    self.work_items = self.items[:]
  def begin(self, rng:Random):
    self.idx = -1
    k = rng.randint(0, len(self.items)-1)
    self.work_items = self.items[-k:] + self.items[:-k]

ItemsWOD()

class ItemsMOD(ItemSet):
  def __init__(self):
    super().__init__("time_month_days", ["time"])
    self.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    self.items = self.months
    self.work_items = self.items[:]

  def begin(self, rng:Random):
    k = rng.randint(0, len(self.months)-1)
    self.work_items = self.months[-k:] + self.months[:-k]

  def getItem(self):
    self.idx += 1
    return f"{self.idx+1} {self.work_items[0]}"

ItemsMOD()

def preProcess():
  for r in ITEMS:
    rule = ItemSet(r["id"], r["category"])
    rule.grp = r["group_name"]
    rule.items = r["items"]

preProcess()

def ItemDB_reset(rng:Random):
  for r in ITEMDB.values():
    r.begin(rng)

def ItemDB_getTimeSeries(rng:Random, N=3):
  t_grps:List[ItemSet] = []
  for r in ITEMDB.values():
    if "time" in r.categories and N <= len(r.items):
      t_grps.append(r)

  return rng.choice(t_grps)

TIME_SHORT = {
  "Monday": "Mon",
  "Tuesday": "Tue",
  "Wednesday": "Wed",
  "Thursday": "Thu",
  "Friday": "Fri",
  "Saturday": "Sat",
  "Sunday": "Sun",

  "January": "Jan",
  "February": "Feb", 
  "March": "Mar",
  "April": "Apr",
  "May": "May",
  "June": "Jun",
  "July": "Jul",
  "August": "Aug",
  "September": "Sep",
  "October": "Oct",
  "November": "Nov",
  "December": "Dec"
}

def ItemDB_getTimeSeriesShort(long:str):
  return TIME_SHORT.get(long, long)