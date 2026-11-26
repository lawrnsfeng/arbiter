import json


class Order:
    def __init__(self, weight: float, rate: float, express: bool, items: list) -> None:
        self.weight = weight
        self.rate = rate
        self.express = express
        self.items = items

    def shipping_cost(self) -> float:
        base = self.weight * self.rate + (5 if self.express else 0)
        return base * 0.9 if len(self.items) > 10 else base


def to_json(order: Order) -> str:  # a serialiser reads every field by design
    return json.dumps({"weight": order.weight, "rate": order.rate, "express": order.express, "items": order.items})


class Checkout:
    def total(self, order: Order, subtotal: float) -> float:
        return subtotal + order.shipping_cost()
