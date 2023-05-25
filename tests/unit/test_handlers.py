import pytest
from allocation.domain import events, model
from allocation.adapters import repository
from allocation.service_layer import handlers, unit_of_work, messagebus
from datetime import date


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

    def _get_by_batchref(self, batchref):
        return next((
            p for p in self._products for b in p.batches
            if b.reference == batchref
        ), None)

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
            event=events.BatchCreated("bb1", "LOLLY-POP", 120, None), uow=uow
        )
        assert uow.products.get("LOLLY-POP") is not None
        assert uow.committed

    def test_existing_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(event=events.BatchCreated(
            "bb1", "LOLLY-POP", 120, None), uow=uow)
        messagebus.handle(event=events.BatchCreated(
            "bb2", "LOLLY-POP", 100, None), uow=uow)
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
            messagebus.handle(events.AllocationRequired("oo1", "NONEXISTENTSKU", 20),
                              uow)

    def test_commit(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated(
            "bb1", "LOLLY-POP", 120, None), uow)
        messagebus.handle(events.AllocationRequired(
            "oo1", "LOLLY-POP", 20), uow)
        assert uow.committed


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            events.BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        [batch] = uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100

        messagebus.handle(events.BatchQuantityChanged("batch1", 50), uow)

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        event_history = [
            events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            events.BatchCreated(
                "batch2", "INDIFFERENT-TABLE", 50, date.today()),
            events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
