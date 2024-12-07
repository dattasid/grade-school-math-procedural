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

# Variation: Plus/Minus

In some problems, the main character will buy and sell a item, or get then give away some item. Thus each line item can be positive or negative. The student must now add or subtract the correct numbers. The main character might start with some items. As a sanity check the running total must never go below zero, though the problem can still be answered with that issue.

# Variation: Relative quantities

Instead of giving a number directly, the problem gives a number as a relation to another (_known_) number.

**Example:** Rani bought 2 apples, then she bought twice as many apples.

**Example:** Half the fruits Rebecca bought were apples. If she bought 20 fruits, and 3 fruits were oranges, how many pears did she buy?

Note that, relations of unknown quantites will cause the problem to become an algrabra problem. It can still be solved with bringing in `x`, but it is complicated and not typical of GSM problems.

**Not suggested:** Kelly bought some apples, twice as many oranges, and two pears. If she bought 20 fruits, how many apples did she buy?

# Variation: Extra information
The Apple paper suggests adding some extraneous information trips up some LLMS and they include the info in the calculations. We can do this in various ways:

1. A different person can buy the same item while the problems asks question about the main character.
2. The main character can buy an unrelated item while the problem asks only about a certain group of items.
  3. The generator must be careful that the item group must exclude the trick item.
3. The problem can ask details about only a subset of people/items days.

**Wrong:** Ram buys 2 cheeze pizza, 3 margherita pizza, and 4 apples. How many items of food did he buy?

**Correct:** Ram buys 2 cheeze pizza, 3 margherita pizza, and 4 apples. How many _pizza_ did he buy?

**Example:** Rahim buys 1 apple, 2 lemons and 4 oranges. How many citrus fruits did he buy?

# Minor variation: modify the answer

The question, sometimes without reason, asks for eg twice the answer, thrice the answer, etc. One common way would be: I bought some items. If I pay X, how much do I get back?

# Variation: The sum of line items, each is a product (usually prices of items problem)

**Example:** Samantha buys 3 apples for $2 each, 4 bananas for $1 each, and 2 oranges for $3 each at the market. How much does she spend in total?

Now each line item is a product of 2 numbers. Either the student must find the total, or find a missing number when the other (eg price and quantity) is given.

A variation from price of items is `sum(x_i sets of y_i items)` eg 2 bags of 3 apples each, 4 bags of 2 oranges each, etc.

Note that this can be compounded with all variations above.

# Variation: More complex products

Instead of price of each item, or buying multiple bags of products, we can have more complex relationships. **Example:** 2 boxes of 3 bags each, each bag of 20 chips. This can be combined with price too.

Other similar relations are:

Library>Shelves>Books>Pages
Cabinet>Shelves>Trays>Cups

Now each lineitem is a product of 3 items.

# Problem type: Subdivision

In this problem, you are given a total. Then you are given groups of the item what fraction is their count. Then again.

The goal is to find the total count or difference of some subgroup.

Example: A school has 100 students. Section A has 60% of the students while section B has the rest. 40% students in section A are male, 30% students in section B are female. How many more girls does section A have than section B?

