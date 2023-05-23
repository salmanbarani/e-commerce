import pytest
from allocation.domain import events
from allocation.adapters import repository
from allocation.service_layer import handlers, unit_of_work, messagebus


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        try:
            return next(p for p in self._products if p.sku == sku)
        except StopIteration:
            return None

    def list(self):
        return list(self._products)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestAddingBatch:
    def test_new_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            event=events.BatchCreated("bb1", "LOLLY-POP", 120, None, uow)
        )
        assert uow.products.get("LOLLY-POP") is not None
        assert uow.committed

    def test_existing_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(event=events.BatchCreated(
            "bb1", "LOLLY-POP", 120, None, uow))
        messagebus.handle(event=events.BatchCreated(
            "bb2", "LOLLY-POP", 100, None, uow))
        assert "bb2" in [
            b.reference for b in uow.products.get("LOLLY-POP").batches]


class TestAllocation:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            events.BatchCreated("bb1", "LOLLY-POP", 120, None), uow
        )
        result = messagebus.handle(
            events.AllocationRequired("oo1", "LOLLY-POP", 20), uow
        )
        assert result.pop(0) == "bb1"

    def test_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated(
            "bb1", "LOLLY-POP", 120, None), uow)
        with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            messagebus.handle(
                events.AllocationRequired(
                    "oo1", "NONEXISTENTSKU", 20, None), uow
            )

    def test_commit(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated(
            "bb1", "LOLLY-POP", 120, None), uow)
        messagebus.handle(events.AllocationRequired(
            "oo1", "LOLLY-POP", 20, None), uow)
        assert uow.committed
