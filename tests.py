from datetime import date


def sample_batch(ref="batch-001", sku="SMALL-TABLE", qty=20, eta=date.today()):
    return Batch(ref, sku, qty, eta)


def sample_line(ref='order-ref', sku='SMALL-TABLE', qty=2):
    return OrderLine(ref, sku, qty)


def test_allocating_to_a_batch_reduce_the_available_quantity():
    batch, line = sample_batch(), sample_line()
    batch.allocate(line)
    assert batch.available_quantity == 18
