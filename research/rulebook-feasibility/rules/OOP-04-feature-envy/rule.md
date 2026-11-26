---
id: OOP-04
title: Feature envy (tell, don't ask)
tier: semantic
severity: should-fix
---
Pattern: a function or method that reads several fields of another object to compute something about that object,
instead of asking the object to do it. The data and the behaviour live apart.

× `def shipping_cost(order): return order.weight * order.zone.rate + (5 if order.express else 0)` outside `Order`
✓ `order.shipping_cost()`, with the computation on `Order`

No syntactic pattern separates this from legitimate code (serialisers, mappers, reports read many fields too), so a
model judges it.
