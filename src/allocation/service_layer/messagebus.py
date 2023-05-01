from allocation.domain import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


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
