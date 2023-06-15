from allocation.service_layer import unit_of_work, messagebus
from allocation.domain import commands
from datetime import date
from allocation import views

today = date.today()


def test_allocations_view(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    messagebus.handle(commands.CreateBatch('sku1batch', 'sku1', 50,
                                           None), uow)
    messagebus.handle(commands.CreateBatch('sku2batch', 'sku2', 50,
                                           today), uow)
    messagebus.handle(commands.Allocate('order1', 'sku1', 20), uow)
    messagebus.handle(commands.Allocate('order1', 'sku2', 20), uow)

    messagebus.handle(commands.CreateBatch('sku1batch-later', 'sku1',
                                           50, today), uow)
    messagebus.handle(commands.Allocate('otherorder', 'sku1', 30), uow)
    messagebus.handle(commands.Allocate('otherorder', 'sku2', 10), uow)
    assert views.allocations('order1', uow) == [
        {'sku': 'sku1', 'batchref': 'sku1batch'}, {
            'sku': 'sku2', 'batchref': 'sku2batch'},
    ]
