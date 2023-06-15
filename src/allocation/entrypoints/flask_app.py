from datetime import datetime
from flask import Flask, request, jsonify
import json
from allocation.domain import model, commands
from allocation.adapters import orm
from allocation.service_layer import handlers, unit_of_work, messagebus
from allocation import views

app = Flask(__name__)
orm.start_mappers()


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    handlers.add_batch(commands.CreateBatch(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta),
        unit_of_work.SqlAlchemyUnitOfWork(),
    )
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        cmd = commands.Allocate(
            request.json['orderid'], request.json['sku'],
            request.json['qty'],
        )
        results = messagebus.handle(cmd, unit_of_work.SqlAlchemyUnitOfWork())
        batchref = results.pop(0)
    except (model.OutOfStock, handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/allocations/<orderid>", methods=["GET"])
def allocations_view_endpoint(orderid):
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    result = views.allocations(orderid, uow)
    if not result:
        return 'not found', 404
    return jsonify(result), 202
