import random
from typing import List, Dict
import re

def getPlural(word:str)->str:
    """
    Converts a singular noun to its plural form using common rules of thumb
    and handles common exceptions.
    """
    # List of common exceptions
    exceptions = {
        "child": "children",
        "man": "men",
        "woman": "women",
        "tooth": "teeth",
        "foot": "feet",
        "mouse": "mice",
        "goose": "geese",
        "person": "people",
        "cactus": "cacti",
        "fungus": "fungi",
        "nucleus": "nuclei",
        "analysis": "analyses",
        "thesis": "theses",
        "crisis": "crises",
        "phenomenon": "phenomena",
        "ox": "oxen"
    }
    common_plural = \
      ["jeans", "pants", "shorts", "scissors", "glasses", "tweezers", "trousers", "clothes",
       "weights", "earnings", "goods", "barracks", "headquarters", "species", "series",
       "socks", "shoes"]

    # Check if the word is an exception
    if word in exceptions:
      return exceptions[word]
    if word in common_plural:
      return word

    # Common pluralization rules
    if word.endswith("y") and word[-2].lower() not in "aeiou":
        # Change "y" to "ies" (e.g., "city" -> "cities")
        return word[:-1] + "ies"
    elif word.endswith(("s", "x", "z", "ch", "sh")):
        # Add "es" to words ending in "s", "x", "z", "ch", or "sh"
        return word + "es"
    elif word.endswith("f"):
        # Change "f" to "ves" (e.g., "wolf" -> "wolves")
        return word[:-1] + "ves"
    elif word.endswith("fe"):
        # Change "fe" to "ves" (e.g., "knife" -> "knives")
        return word[:-2] + "ves"
    elif word.endswith("o"):
        # Add "es" to some words ending in "o" (e.g., "potato" -> "potatoes")
        return word + "es"
    else:
        # Default: Add "s" (e.g., "cat" -> "cats")
        return word + "s"


# Examples of usage
# print(getPlural("child"))     # Output: children
# print(getPlural("city"))      # Output: cities
# print(getPlural("box"))       # Output: boxes
# print(getPlural("wolf"))      # Output: wolves
# print(getPlural("potato"))    # Output: potatoes
# print(getPlural("cat"))       # Output: cats
# print(getPlural("person"))    # Output: people

class Verb:
  def __init__(self, base:str, past:str, past_p:str):
    self.base = base
    self.past = past
    self.past_p = past_p

VERBS = [
   Verb("eat", "ate", "eaten"),
   Verb("buy", "bought", "bought"),
   Verb("sell", "sold", "sold"),
   Verb("walk", "walked", "walked"),
   Verb("run", "ran", "run"),
   Verb("travel", "traveled", "traveled"),
]

VERBS_HT = { verb.base:verb for verb in VERBS }

def replace_variables(s:str, vars: Dict[str, str]):

    # print(s, " *** ", vars)

    def replace(match:str):
    #   print (f"Replacing {match}")
      if match in vars:
        return str(vars[match])
      else:
        return "Error_"+match

      
    # Find all occurrences of $key in the string
    # return re.sub(r'\$(\w+)', lambda match: replace(match.group(1)), s)
    return re.sub(r'(?<!\\)\$(\w+)', lambda match: replace(match.group(1)), s)


def join_with_and(l:List[str])->str:
  if len(l) == 1:
    return l[0]
  return ", ".join(l[:-1]) + " and " + l[-1]

MALE_NAMES = ["James", "Michael", "William", "Ethan", "Alexander", "Daniel", "Henry", "Jackson", "Logan", "Lucas", "Alejandro", "Diego", "Javier", "Carlos", "Antonio", "Manuel", "Miguel", "Pablo", "Rafael", "Luis", "Liam", "Noah", "Matteo", "Luca", "Maximilian", "Olivier", "Jonas", "Sebastian", "Nikola", "Viktor", "Wei", "Liang", "Jun", "Jie", "Xiao", "Lei", "Ming", "Tao", "Cheng", "Liu", "Rui", "Ping", "Zhi", "Haruto", "Ren", "Yuto", "Souta", "Riku", "Itsuki", "Yuki", "Takumi", "Kaito", "Ryota", "Aarav", "Vihaan", "Aditya", "Arjun", "Karan", "Vivaan", "Rahul", "Rohan", "Krishna", "Aryan", "Anong", "Niran", "Chai", "Kawin", "Somchai", "Thanh", "Phichai", "Ashkii", "Supalak", "Kwame", "Kofi", "Omari", "Taye", "Chinwe", "Oba", "Ade", "Kamau", "Simba", "Femi", "Jabari"]
FEMALE_NAMES = ["Emma", "Olivia", "Sophia", "Ava", "Mia", "Charlotte", "Amelia", "Harper", "Ella", "Grace", "Sofia", "Lucia", "Martina", "Isabella", "Valeria", "Camila", "Maria", "Gabriela", "Elena", "Natalia", "Hannah", "Amelie", "Lea", "Anna", "Eva", "Mei", "Ying", "Lan", "Fang", "Hua", "Yan", "Shan", "Sakura", "Aoi", "Hana", "Rin", "Mio", "Nana", "Akari", "Hinata", "Aya", "Yuna", "Ishani", "Anaya", "Riya", "Kavya", "Priya", "Sneha", "Pooja", "Meera", "Nidhi", "Shruti", "Mai", "Dakota", "Thao", "Aiyana", "Linh", "Tala", "Hoa", "Nokomis", "Makya", "Hanh", "Chi", "Amina", "Zuri", "Amara", "Sade", "Nia", "Ngozi", "Binta", "Zola", "Imani"]


def replace_name_with_pronoun(q_lines:List[str], name:str, pronoun:str):
  """Replace names with pronouns"""
  seen_name = False
  pronoun_l = pronoun.lower()
  pronoun_u = pronoun.capitalize()
  for idx, line in enumerate(q_lines):
    if seen_name:
      if line.startswith(name):
        q_lines[idx] = line.replace(name, pronoun_u)
      else:
        q_lines[idx] = line.replace(name, pronoun_l)
      # Very inefficient. optimize?
      
    elif name in line:
      seen_name = True
      continue

def cleanup_str(s:str)->str:
  s = re.sub(r' +', ' ', s)
  s = re.sub(r'\.+', '.', s)
  s = re.sub(r'\\\$', '$', s)
  return s



def num_to_price(n:int)->str:
  """ Convert a number like 123 to 1.23"""
  s = str(n)
  if len(s) < 2:
    return ".0"+s
  elif len(s) < 3:
    return f".{s}"
  else:
    return f"{s[:-2]}.{s[-2:]}"

# Basically itemset with less steps
class ShuffledList:
  def __init__(self,  rand: random.Random, *values:str):
    self.values = list(values)
    rand.shuffle(self.values)
    self.idx = -1

  def next(self)->str:
    self.idx = (self.idx + 1) % len(self.values)
    return self.values[self.idx]


# a = ShuffledList(random.Random(), "a", "b")
