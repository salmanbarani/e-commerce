import pytest
from allocation.domain import model
from allocation.service_layer import unit_of_work
from sqlalchemy import text


def insert_product(session, sku):
    session.execute(
        text("INSERT INTO products (sku)"
             " VALUES (:sku)"),
        dict(sku=sku),
    )


def test_uow_can_retrieve_product(session_factory):
    session = session_factory()
    insert_product(session, "sku_")
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        product = uow.products.get(sku="sku_")
        assert product.sku == "sku_"


def test_uow_can_save_product(session_factory):
    session = session_factory()
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        uow.products.add(model.Product("sku_to_be_saved", []))
        uow.commit()

    product = session.query(model.Product).filter_by(
        sku="sku_to_be_saved").one()
    assert product.sku == "sku_to_be_saved"


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_product(uow.session, "product_sku")

    new_session = session_factory()
    rows = list(new_session.execute(text('SELECT * FROM "products"')))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_product(uow.session, "product_sku")
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute(text('SELECT * FROM "products"')))
    assert rows == []
