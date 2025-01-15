# Example of 'normal' question.

### Data presentation varies to test the model's attention.

On Monday, Hanh bought 0 less Mushroom Pizzas than Tuesday for two times the price as Tuesday each.
Hanh bought 44 Mushroom Pizzas on Tuesday for six dollars zero cents each.
Hanh bought one half as many Mushroom Pizzas as Monday for five times the price as Thursday per item on Wednesday.
On Thursday, Hanh paid 150% the price as Monday per item for 1/2th the Mushroom Pizzas as Tuesday.
Hanh paid double the price as Monday per item for 2 times as many Mushroom Pizzas as Monday on Friday.
What was the total amount Hanh spent?
---

### Example answer, can be used for debugging.
Note that the answer assumes the model can decide which variables have all their dependencies determined and hence can be calculated right now.


Let us think step by step.
In this problem we see there the person buying only one type of item. The quantity and price varies over time. Let us denote this by Q_day and P_day.
Let us rewrite the problem in a simpler manner.
```
Q_Monday = Q_Tuesday+0. P_Monday = P_Tuesday*2.
Q_Tuesday = 44. P_Tuesday = 600.
Q_Wednesday = Q_Monday/2. P_Wednesday = P_Thursday*5.
Q_Thursday = Q_Tuesday/2. P_Thursday = P_Monday*3/2.
Q_Friday = Q_Monday*2. P_Friday = P_Monday*2.
Q_Tuesday = 44
Q_Monday = Q_Tuesday+0 = 44+0 = 44
Q_Wednesday = Q_Monday/2 = 44/2 = 22
Q_Thursday = Q_Tuesday/2 = 44/2 = 22
Q_Friday = Q_Monday*2 = 44*2 = 88
P_Tuesday = 6.00
P_Monday = P_Tuesday*2 = 6.00*2 = 12.00
P_Thursday = P_Monday*3/2 = 12.00*3/2 = 18.00
P_Friday = P_Monday*2 = 12.00*2 = 24.00
P_Wednesday = P_Thursday*5 = 18.00*5 = 90.00
Spent on Monday: 44 * $12.00 = $528.00
Spent on Tuesday: 44 * $6.00 = $264.00
Spent on Wednesday: 22 * $90.00 = $1980.00
Spent on Thursday: 22 * $18.00 = $396.00
Spent on Friday: 88 * $24.00 = $2112.00
Total: $528.00 + $264.00 + $1980.00 + $396.00 + $2112.00 = $5280.00
#### 5280.00
```
