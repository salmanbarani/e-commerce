import pytest
from allocation.adapters import repository
from allocation.service_layer import services, unit_of_work


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


def test_add_batch_to_new_product():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_add_batch_to_existing_product():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)
    services.add_batch("b2", "COMPLICATED-LAMP", 50, None, uow)
    assert "b2" in [b.reference for b in uow.products.get(
        "COMPLICATED-LAMP").batches]


def test_allocate_method_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", 100, None, uow)
    result = services.allocate("o1", "AREALSKU", 10, uow)
    assert result == "b1"


def test_allocate_raise_erros_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, None, uow)
    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTINGSKU"):
        services.allocate("01", "NONEXISTINGSKU", 5, uow)


def test_allocate_commits():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, None, uow)
    services.allocate("01", "OMINOUS-MIRROR", 9, uow)
    assert uow.committed
