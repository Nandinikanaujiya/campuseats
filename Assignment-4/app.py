"""
CampusEats Orders Microservice (REST)
CS 543 Web Services · Assignment 4
Team 10: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra

Endpoints implemented:
1. POST /orders                  - Create order with idempotency & outbound payment
2. GET  /orders/<id>             - Read single order representation
3. GET  /orders                  - Filtered collection query
4. POST /orders/<id>/cancellation - State-changing sub-resource
"""

import os
from flask import Flask, request, jsonify, make_response
from models import Order, validate_order_payload, validate_cancellation_payload, is_valid_uuid
from store import store
from errors import problem
from client import payment_client, PaymentRefusedError, PaymentGatewayUnavailableError

app = Flask(__name__)


# -----------------------------------------------------------------------------
# 1. CREATE ORDER (POST /orders)
# -----------------------------------------------------------------------------
@app.route("/orders", methods=["POST"])
def create_order():
    # Parse JSON body
    if not request.is_json:
        return problem(
            status=400,
            title="Bad Request",
            detail="Content-Type must be application/json with valid JSON body.",
            instance="/orders"
        )

    try:
        data = request.get_json()
    except Exception as e:
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Malformed JSON payload: {str(e)}",
            instance="/orders"
        )

    # Requirement C4: Validate body before touching fields
    is_valid, error_msg, err_status = validate_order_payload(data)
    if not is_valid:
        title = "Unprocessable Entity" if err_status == 422 else "Bad Request"
        return problem(
            status=err_status,
            title=title,
            detail=error_msg,
            instance="/orders"
        )

    # Requirement C7: Idempotency-Key header support
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        cached_record = store.get_idempotency_record(idempotency_key)
        if cached_record:
            # Safely return identical original response without re-charging card or duplicating order
            response = make_response(jsonify(cached_record["body"]), cached_record["status_code"])
            response.headers["Content-Type"] = "application/json"
            response.headers["Location"] = cached_record["location"]
            response.headers["X-Cache-Lookup"] = "HIT-IDEMPOTENT"
            return response

    # Instantiate Order (Requirement C2: internal record separation)
    order = Order(
        customer_id=data["customer_id"],
        canteen_id=data["canteen_id"],
        items=data["items"],
        delivery_fee=data.get("delivery_fee", 30.00),
        payment_token=data.get("payment_token"),
        custom_notes=data.get("custom_notes")
    )

    # Requirement D1 & D2: Outbound call to Payments service
    try:
        payment_client.charge(
            order_id=order.id,
            amount=order.total_price,
            customer_id=order.customer_id,
            payment_token=order.raw_payment_token,
            idempotency_key=idempotency_key
        )
    except PaymentRefusedError as pe:
        # Domain refusal from payment partner
        return problem(
            status=422,
            title="Payment Declined",
            detail=f"Upstream payment was declined: {pe.detail}",
            instance=f"/orders/{order.id}"
        )
    except PaymentGatewayUnavailableError as pge:
        # Requirement D3 Fallback: Fail fast with 502 rather than degrading
        return problem(
            status=502,
            title="Bad Gateway",
            detail=f"Payment processing failed: {str(pge)}",
            instance=f"/orders/{order.id}"
        )

    # Save to store
    representation = order.as_json()
    location_url = f"/orders/{order.id}"

    cached_payload = {
        "body": representation,
        "status_code": 201,
        "location": location_url
    }
    store.save(order, idempotency_key=idempotency_key, cached_response=cached_payload)

    # Requirement C5: 201 Created with Location header
    response = make_response(jsonify(representation), 201)
    response.headers["Content-Type"] = "application/json"
    response.headers["Location"] = location_url
    return response


# -----------------------------------------------------------------------------
# 2. READ SINGLE ORDER (GET /orders/<id>)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Order identifier '{order_id}' is not a valid UUID format.",
            instance=f"/orders/{order_id}"
        )

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            title="Not Found",
            detail=f"Order with ID '{order_id}' was not found in the catalogue.",
            instance=f"/orders/{order_id}"
        )

    return jsonify(order.as_json()), 200


# -----------------------------------------------------------------------------
# 3. FILTERED ORDER LIST (GET /orders)
# -----------------------------------------------------------------------------
@app.route("/orders", methods=["GET"])
def list_orders():
    customer_id = request.args.get("customer_id")
    status = request.args.get("status")

    if customer_id and not is_valid_uuid(customer_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Query parameter 'customer_id' must be a valid UUID.",
            instance="/orders"
        )

    valid_statuses = {"placed", "preparing", "ready_for_pickup", "out_for_delivery", "delivered", "cancelled"}
    if status and status not in valid_statuses:
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Query parameter 'status' must be one of {sorted(list(valid_statuses))}.",
            instance="/orders"
        )

    orders = store.list_all(customer_id=customer_id, status=status)
    return jsonify({
        "orders": [o.as_json() for o in orders],
        "count": len(orders)
    }), 200


# -----------------------------------------------------------------------------
# 4. STATE-CHANGING SUB-RESOURCE (POST /orders/<id>/cancellation)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>/cancellation", methods=["POST"])
def cancel_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Order identifier '{order_id}' is not a valid UUID format.",
            instance=f"/orders/{order_id}/cancellation"
        )

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            title="Not Found",
            detail=f"Cannot cancel non-existent order with ID '{order_id}'.",
            instance=f"/orders/{order_id}/cancellation"
        )

    # State Conflict (Requirement C5: 409 Conflict)
    if order.status == "cancelled":
        return problem(
            status=409,
            title="State Conflict",
            detail=f"Order '{order_id}' has already been cancelled previously.",
            instance=f"/orders/{order_id}/cancellation"
        )

    if order.status in ("delivered", "out_for_delivery"):
        return problem(
            status=409,
            title="State Conflict",
            detail=f"Cannot cancel order '{order_id}' because it is already {order.status}.",
            instance=f"/orders/{order_id}/cancellation"
        )

    # Validate cancellation payload
    data = request.get_json(silent=True) or {}
    is_valid, err_msg, _ = validate_cancellation_payload(data)
    if not is_valid:
        return problem(
            status=400,
            title="Bad Request",
            detail=err_msg,
            instance=f"/orders/{order_id}/cancellation"
        )

    # Execute state change
    order.cancel(reason=data["reason"])
    return jsonify(order.as_json()), 200


# -----------------------------------------------------------------------------
# GLOBAL ERROR HANDLERS (Requirement C6)
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def handle_404(e):
    return problem(
        status=404,
        title="Not Found",
        detail="The requested resource or endpoint path was not found on this server.",
        instance=request.path
    )


@app.errorhandler(405)
def handle_405(e):
    return problem(
        status=405,
        title="Method Not Allowed",
        detail=f"HTTP method '{request.method}' is not supported for endpoint '{request.path}'.",
        instance=request.path
    )


@app.errorhandler(500)
def handle_500(e):
    return problem(
        status=500,
        title="Internal Server Error",
        detail="An unexpected internal server error occurred while processing the request.",
        instance=request.path
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
