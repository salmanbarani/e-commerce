from datetime import date
from dataclasses import dataclass


class Batch:
    def __init__(self, ref, sku, qty, eta) -> None:
        self.ref = ref
        self.sku = sku
        self.qty = qty
        self.eta = eta

    def allocate(self, order_line):
        if self.sku == order_line.sku and self.qty >= order_line.qty:
            self.qty -= order_line.qty
        return True


@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int
