from allocation.domain import events
from . import unit_of_work


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


# HANDLERS contains list of callables for each event type
HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification]
}
