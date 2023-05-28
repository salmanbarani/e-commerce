from __future__ import annotations
from allocation.domain import events, commands
from . import handlers
from typing import List, Union, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from . import unit_of_work

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
            # no need to collecte event results
        elif isinstance(message, commands.Command):
            cmd_results = handle_command(message, queue, uow)
            results.append(cmd_results)
        else:
            raise Exception(f"{message} wasn't an Event or Command.")
    return results


def handle_event(
    event: events.Event,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork
):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug("handing event %s with handler %s", event, handler)
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception("Exception handing event  %s", event)
            continue


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork
):
    logger.debug("handing command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception("Exception handing event  %s", command)
        raise


def send_email(send_to, message):
    print(f'Email was sent to {send_to}, \n Message: {message}')


def send_out_of_stock_notification(event: events.OutOfStock):
    send_email(
        'stock@e-commerce.com',
        f'Out of stock {event.sku}'
    )


EVENT_HANDLERS = {
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.AllocationRequired: [handlers.allocate],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}

COMMAND_HANDLERS = {
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}
