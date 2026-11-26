class Zone:
    def __init__(self, rate: float) -> None:
        self.rate = rate


class Order:
    def __init__(self, weight: float, zone: Zone, express: bool, items: list) -> None:
        self.weight = weight
        self.zone = zone
        self.express = express
        self.items = items


class Checkout:
    def shipping_cost(self, order: Order) -> float:  # expect: OOP-04
        base = order.weight * order.zone.rate
        if order.express:
            base += 5
        if len(order.items) > 10:
            base *= 0.9
        return base


def is_bulk(order: Order) -> bool:  # expect: OOP-04
    return len(order.items) > 10 and order.weight > 50 and not order.express
