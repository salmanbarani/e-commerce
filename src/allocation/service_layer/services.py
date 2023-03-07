from allocation.domain.model import OrderLine
from allocation.adapters.repository import AbstractRepository
from allocation.domain import model


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")
    batchref = model.allocate(batches)
    session.commit()
    return batchref


def deallocate(line: OrderLine, batchrf, repo: AbstractRepository, session) -> str:
    batches = repo.get(batchrf)
    batches.deallocate(line)
    session.commit()
    return True
