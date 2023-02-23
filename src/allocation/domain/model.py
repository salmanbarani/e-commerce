from dataclasses import dataclass
from datetime import date
from typing import Optional


class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()

    def can_allocate(self, line):
        if self.available_quantity >= line.qty and self.sku == line.sku:
            return True
        return False

    def allocate(self, line):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def __gt__(self, __o: object) -> bool:
        if self.eta is None:
            return False
        if __o.eta is None:
            return True
        return self.eta > __o.eta

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self.__class__):
            return False
        return self.reference == __o.reference

    def __hash__(self) -> int:
        return hash(self.reference)


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


def allocate(line: OrderLine, batches: Optional[Batch]):
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")


class OutOfStock(Exception):
    pass