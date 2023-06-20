from allocation.service_layer import unit_of_work
from sqlalchemy import text

def allocations(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = uow.session.execute( text(
            """
            SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid
            """),
            dict(orderid=orderid),
        )
    result_list = results.fetchall() 
    return [{column: value for column, value in zip(results.keys(), row)} for row in result_list]
