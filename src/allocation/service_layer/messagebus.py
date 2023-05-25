from allocation.domain import events
from . import unit_of_work
from . import handlers


def handle(event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow))
            queue.extend(uow.collect_new_events())
    return results


def send_email(send_to, message):
    print(f'Email was sent to {send_to}, \n Message: {message}')


def send_out_of_stock_notification(event: events.OutOfStock):
    send_email(
        'stock@e-commerce.com',
        f'Out of stock {event.sku}'
    )


HANDLERS = {
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.AllocationRequired: [handlers.allocate],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}
