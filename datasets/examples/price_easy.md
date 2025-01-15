### Example of 'easy' question.

_Data presentation varies to test the model's attention._

On Friday, Logan bought 4/3 th the BBQ Chicken Pizzas as Tuesday.<br>
On Saturday, Logan bought 4x the BBQ Chicken Pizzas as Monday. On Saturday, Logan paid $8.00 per BBQ Chicken Pizza.<br>
On Sunday, Logan bought 1/4 th the BBQ Chicken Pizzas as Friday. On Sunday, Logan paid 3x the price as Saturday per BBQ Chicken Pizza.<br>
On Monday, Logan bought 11 less BBQ Chicken Pizzas than Friday. On Monday, Logan paid 2x the price as Saturday per BBQ Chicken Pizza.<br>
On Tuesday, Logan bought 45 BBQ Chicken Pizzas. On Tuesday, Logan paid 7/4 th the price as Monday per BBQ Chicken Pizza.<br>
Logan spent a total of five Thousand four Hundred twelve dollars zero cents.<br>
What did Logan spend per BBQ Chicken Pizza for Friday?<br>

---

_Example answer, can be used for debugging._
_Note that the answer assumes the model can decide which variables have all their dependencies determined and hence can be calculated right now._


Let us think step by step.
In this problem we see there the person buying only one type of item. The quantity and price varies over time. Let us denote this by Q_day and P_day.
Let us rewrite the problem in a simpler manner.

```
Q_Friday = Q_Tuesday*4/3.
Q_Saturday = Q_Monday*4. P_Saturday = 800.
Q_Sunday = Q_Friday/4. P_Sunday = P_Saturday*3.
Q_Monday = Q_Friday-11. P_Monday = P_Saturday*2.
Q_Tuesday = 45. P_Tuesday = P_Monday*7/4.
Q_Tuesday = 45
Q_Friday = Q_Tuesday*4/3 = 45*4/3 = 60
Q_Sunday = Q_Friday/4 = 60/4 = 15
Q_Monday = Q_Friday-11 = 60-11 = 49
Q_Saturday = Q_Monday*4 = 49*4 = 196
P_Saturday = 8.00
P_Sunday = P_Saturday*3 = 8.00*3 = 24.00
P_Monday = P_Saturday*2 = 8.00*2 = 16.00
P_Tuesday = P_Monday*7/4 = 16.00*7/4 = 28.00
Spent on Saturday: 196 * $8.00 = $1568.00
Spent on Sunday: 15 * $24.00 = $360.00
Spent on Monday: 49 * $16.00 = $784.00
Spent on Tuesday: 45 * $28.00 = $1260.00
Total except Friday: $1568.00 + $360.00 + $784.00 + $1260.00 = $5412.00
Spent on Friday: $5412.00 - $3972.00 = $1440.00
Price on Friday: 1440.00 / 60 = $24.00
#### 24.00
```

