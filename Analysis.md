# Introduction

Here we note down the typical GSM problems and their variations.

# The sum of line items problem.

This problem can be summarized as: `sum(x_i)=T`, where either one x_i or T will be missing. The object is to find the missing number. There is some minor common sense set relationship tests also, more on this later.

**Example:**
Renee bought 5 apples, 6 oranges and 7 peaches. How many fruits did he buy?

**Example:**
Ravi bought 4 apples, 7 pears and some lychee. If he bought 15 fruits in total, how many lychee did he buy?

They can buy items (most common), eat food, walk miles, or perform other countable activities.

# Variation: Changing situation using different names, days, etc.

Instead of different types of fruits, the kids can buy the same fruit on different days. Or multiple kids can buy an item. 

**Example:**
Alex eats 3 apples on Monday, 2 apples on Wednesday, and 4 apples on Friday. How many apples does Alex eat in total?

**Example:**
Alex, Bella, and Charlie go to a toy store. They each buy toy cars:
Alex buys 3 toy cars.
Bella buys 5 toy cars.
Charlie buys 7 toy cars.
How many toy cards total did they buy?

# Variation: Extra information
The Apple paper suggests adding some extraneous information trips up some LLMS and they include the info in the calculations. We can do this in various ways:

1. A different person can buy the same item while the problems asks question about the main character.
2. The main character can buy an unrelated item while the problem asks only about a certain group of items.
  3. The generator must be careful that the item group must exclude the trick item.
3. The problem can ask details about only a subset of people/items days.

**Wrong:** Ram buys 2 cheeze pizza, 3 margherita pizza, and 4 apples. How many items of food did he buy?

**Correct:** Ram buys 2 cheeze pizza, 3 margherita pizza, and 4 apples. How many _pizza_ did he buy?

**Example:** Rahim buys 1 apple, 2 lemons and 4 oranges. How many citrus fruits did he buy?

# Variation: The sum of line items, each is a product (usually prices of items problem)




