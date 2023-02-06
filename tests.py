from datetime import date, datetime, timedelta
from model import Batch, OrderLine, allocate, OutOfStock
import pytest


BATCH_REF = 'batch-001'
ORDER_REF = 'order-123'


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch(BATCH_REF, sku, batch_qty, eta=date.today()),
        OrderLine(ORDER_REF, sku, line_qty)
    )


TODAY = datetime.now()
TOMORROW = (TODAY + timedelta(days=1))
LATER = (TODAY + timedelta(days=7))


def test_allocating_to_a_batch_reduce_the_available_quantity():
    batch, line = make_batch_and_line("BIG CHAIR", 20, 2)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    batch, line = make_batch_and_line("BIG CHAIR", 20, 2)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    small_batch, large_line = make_batch_and_line("BIG CHAIR", 20, 25)
    assert small_batch.can_allocate(large_line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line("BIG CHAIR", 20, 20)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch("batch-001", "UNCOMFORTABLE-CHAIR", 100, eta=None)
    different_sku_line = OrderLine("order-123", "EXPENSIVE-TOASTER",
                                   10)
    assert batch.can_allocate(different_sku_line) is False


def test_can_only_dealocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line("GAMING-CHAIR", 200, 20)
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 200


def test_allocation_is_idempotent():
    batch, line = make_batch_and_line("SHIP_TOY", 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100,
                           eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100,
                           eta=TOMORROW)

    line = OrderLine("oref", "RETRO-CLOCK", 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100,
                     eta=TODAY)
    medium = Batch("normal-batch", "MINIMALIST-SPOON", 100,
                   eta=TOMORROW)
    latest = Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=LATER)
    line = OrderLine("order1", "MINIMALIST-SPOON", 10)

    allocate(line, [earliest, medium, latest])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER",
                           100, eta=None)
    shipment_batch = Batch("shipment-batch-ref", "HIGHBROW-POSTER",
                           100, eta=TOMORROW)
    line = OrderLine("oref", "HIGHBROW-POSTER", 10)

    allocation = allocate(line, [in_stock_batch, shipment_batch])
    assert in_stock_batch.reference == allocation


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch('batch1', 'SMALL-FORK', 10, eta=TODAY)
    allocate(OrderLine('order1', 'SMALL-FORK', 10), [batch])

    with pytest.raises(OutOfStock, match='SMALL-FORK'):
        allocate(OrderLine('order2', 'SMALL-FORK', 1), [batch])
