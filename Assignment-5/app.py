"""
CampusEats Orders Microservice (REST)
CS 543 Web Services · Assignment 5
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra

Part A: Methods & the message (CRUD + Non-CRUD sub-resources, OPTIONS + Allow, Method Override)
Part B: Headers on every message (Content-Type, Location, Bearer Auth, ETag, Cache-Control, Rate Limit, CORS)
Part C: Caching & safe retries (Conditional GET 304, Conditional Write 412, Idempotency-Key)
"""

import os
from flask import Flask, request, jsonify, make_response, Response, g
from models import Order, validate_order_payload, validate_update_payload, validate_cancellation_payload, is_valid_uuid
from store import store
from errors import problem
from client import payment_client, PaymentRefusedError, PaymentGatewayUnavailableError

# -----------------------------------------------------------------------------
# Method Override Middleware for constrained clients (A5)
# -----------------------------------------------------------------------------
class MethodOverrideMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        if environ.get("REQUEST_METHOD") == "POST":
            override = environ.get("HTTP_X_HTTP_METHOD_OVERRIDE")
            if override and override.upper() in ("PUT", "DELETE", "PATCH"):
                environ["REQUEST_METHOD"] = override.upper()
        return self.wsgi_app(environ, start_response)


app = Flask(__name__)
app.wsgi_app = MethodOverrideMiddleware(app.wsgi_app)



# -----------------------------------------------------------------------------
# REQUEST HOOKS: Method Override, Content Negotiation, Auth, Rate Limiting
# -----------------------------------------------------------------------------
@app.before_request
def process_incoming_request():
    # A5: X-HTTP-Method-Override support for constrained clients
    if request.method == "POST" and "X-HTTP-Method-Override" in request.headers:
        override = request.headers["X-HTTP-Method-Override"].upper()
        if override in ["PUT", "DELETE", "PATCH"]:
            request.environ["REQUEST_METHOD"] = override

    # B5: Rate limit check (60 req/min per client)
    rate_limit = int(os.environ.get("RATE_LIMIT_PER_MINUTE", 60))
    client_id = request.headers.get("Authorization", request.remote_addr or "anonymous")
    allowed, remaining, retry_after = store.check_rate_limit(client_id, limit=rate_limit)
    g.rate_limit = rate_limit
    g.rate_remaining = remaining

    if not allowed:
        return problem(
            status=429,
            title="Too Many Requests",
            detail=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            extra_headers={"Retry-After": str(retry_after)}
        )

    # B1: Content negotiation — check Accept header
    accept = request.headers.get("Accept")
    if accept and request.method != "OPTIONS":
        if not any(m in accept for m in ["application/json", "application/problem+json", "*/*", "application/*"]):
            return problem(406, "Not Acceptable", "Supported media type: application/json.")

    # B3: Authorization check on state-changing endpoints
    needs_auth = (
        (request.path == "/orders" and request.method == "POST") or
        (request.path.startswith("/orders/") and request.method in ["PUT", "DELETE"]) or
        request.path.endswith("/cancel")
    )
    if needs_auth:
        auth = request.headers.get("Authorization", "").strip()
        if not auth.startswith("Bearer ") or not auth.replace("Bearer ", "").strip():
            return problem(
                status=401,
                title="Unauthorized",
                detail="Missing or empty Bearer token in Authorization header.",
                extra_headers={"WWW-Authenticate": 'Bearer realm="CampusEats Orders API"'}
            )


@app.after_request
def add_response_headers(response: Response) -> Response:
    # B7: Security & standard headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Server"] = "CampusEats-OrdersService/2.0"

    # B6: CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, If-None-Match, If-Match, Idempotency-Key, X-HTTP-Method-Override"
    response.headers["Access-Control-Expose-Headers"] = "Location, ETag, X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After"

    # B5: Rate limit headers
    if hasattr(g, "rate_limit"):
        response.headers["X-RateLimit-Limit"] = str(g.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(g.rate_remaining)

    return response


# -----------------------------------------------------------------------------
# OPTIONS HANDLERS (Requirement A5)
# -----------------------------------------------------------------------------
@app.route("/orders", methods=["OPTIONS"])
def options_orders():
    res = make_response("", 204)
    res.headers["Allow"] = "GET, POST, OPTIONS, HEAD"
    return res


@app.route("/orders/<order_id>", methods=["OPTIONS"])
def options_order_item(order_id: str):
    res = make_response("", 204)
    res.headers["Allow"] = "GET, PUT, DELETE, OPTIONS, HEAD"
    return res


# -----------------------------------------------------------------------------
# 1. CREATE ORDER (POST /orders)
# -----------------------------------------------------------------------------
@app.route("/orders", methods=["POST"])
def create_order():
    if not request.is_json:
        return problem(400, "Bad Request", "Content-Type must be application/json with valid JSON.")

    try:
        data = request.get_json()
    except Exception as e:
        return problem(400, "Bad Request", f"Malformed JSON: {str(e)}")

    is_valid, err_msg, status_code = validate_order_payload(data)
    if not is_valid:
        title = "Unprocessable Entity" if status_code == 422 else "Bad Request"
        return problem(status_code, title, err_msg)

    # C3: Idempotency-Key check
    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        cached = store.get_idempotency_record(idem_key)
        if cached:
            res = make_response(jsonify(cached["body"]), cached["status_code"])
            res.headers["Content-Type"] = "application/json"
            res.headers["Location"] = cached["location"]
            res.headers["ETag"] = cached["etag"]
            res.headers["X-Cache-Lookup"] = "HIT-IDEMPOTENT"
            return res

    order = Order(
        customer_id=data["customer_id"],
        canteen_id=data["canteen_id"],
        items=data["items"],
        delivery_fee=data.get("delivery_fee", 30.00),
        payment_token=data.get("payment_token"),
        custom_notes=data.get("custom_notes")
    )

    try:
        payment_client.charge(
            order_id=order.id,
            amount=order.total_price,
            customer_id=order.customer_id,
            payment_token=order.raw_payment_token,
            idempotency_key=idem_key
        )
    except PaymentRefusedError as pe:
        return problem(422, "Payment Declined", f"Upstream payment declined: {pe.detail}")
    except PaymentGatewayUnavailableError as pge:
        return problem(502, "Bad Gateway", f"Payment gateway unavailable: {str(pge)}")

    rep = order.as_json()
    location = f"/orders/{order.id}"
    etag = order.compute_etag()

    store.save(order, idempotency_key=idem_key, cached_response={
        "body": rep,
        "status_code": 201,
        "location": location,
        "etag": etag
    })

    # B2: 201 Created with Location and ETag headers
    res = make_response(jsonify(rep), 201)
    res.headers["Content-Type"] = "application/json"
    res.headers["Location"] = location
    res.headers["ETag"] = etag
    return res


# -----------------------------------------------------------------------------
# 2. READ SINGLE ORDER (GET /orders/<id>)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.")

    current_etag = order.compute_etag()

    # C1: Conditional GET via If-None-Match -> 304 Not Modified
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match:
        etags = [e.strip() for e in if_none_match.split(",")]
        if "*" in etags or current_etag in etags:
            res = make_response("", 304)
            res.headers["ETag"] = current_etag
            res.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
            return res

    # B4: Cache a read with ETag & Cache-Control
    res = make_response(jsonify(order.as_json()), 200)
    res.headers["Content-Type"] = "application/json"
    res.headers["ETag"] = current_etag
    res.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
    return res


# -----------------------------------------------------------------------------
# 3. LIST ORDERS (GET /orders)
# -----------------------------------------------------------------------------
@app.route("/orders", methods=["GET"])
def list_orders():
    cust_id = request.args.get("customer_id")
    status = request.args.get("status")
    sort = request.args.get("sort", "ordered_at_desc")

    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 10))))
    except ValueError:
        return problem(400, "Bad Request", "page and limit must be integers.")

    if cust_id and not is_valid_uuid(cust_id):
        return problem(400, "Bad Request", "customer_id must be a valid UUID.")

    orders, total = store.list_all(customer_id=cust_id, status=status, sort_by=sort, page=page, limit=limit)

    res = make_response(jsonify({
        "orders": [o.as_json() for o in orders],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit
        }
    }), 200)
    res.headers["Content-Type"] = "application/json"
    res.headers["Cache-Control"] = "no-store"
    return res


# -----------------------------------------------------------------------------
# 4. CONDITIONAL WRITE (PUT /orders/<id>)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["PUT"])
def update_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.")

    # C2: If-Match required for optimistic concurrency
    if_match = request.headers.get("If-Match")
    current_etag = order.compute_etag()

    if not if_match or (if_match != "*" and current_etag not in [e.strip() for e in if_match.split(",")]):
        return problem(412, "Precondition Failed", "If-Match ETag mismatch or missing.")

    if order.status in ["delivered", "cancelled"]:
        return problem(409, "State Conflict", f"Cannot update order with status '{order.status}'.")

    data = request.get_json(silent=True) or {}
    is_valid, err_msg, code = validate_update_payload(data)
    if not is_valid:
        return problem(code, "Bad Request", err_msg)

    order.replace(data)
    new_etag = order.compute_etag()

    res = make_response(jsonify(order.as_json()), 200)
    res.headers["Content-Type"] = "application/json"
    res.headers["ETag"] = new_etag
    return res


# -----------------------------------------------------------------------------
# 5. DELETE ORDER (DELETE /orders/<id>)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.")

    if order.status in ["preparing", "out_for_delivery", "delivered"]:
        return problem(409, "State Conflict", f"Cannot delete active order with status '{order.status}'.")

    store.delete(order_id)
    return make_response("", 204)


# -----------------------------------------------------------------------------
# 6. NON-CRUD ACTION SUB-RESOURCE (POST /orders/<id>/cancel)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.")

    if order.status == "cancelled":
        return problem(409, "State Conflict", "Order is already cancelled.")

    if order.status in ["delivered", "out_for_delivery"]:
        return problem(409, "State Conflict", f"Cannot cancel order in status '{order.status}'.")

    data = request.get_json(silent=True) or {}
    is_valid, err_msg, _ = validate_cancellation_payload(data)
    if not is_valid:
        return problem(400, "Bad Request", err_msg)

    order.cancel(reason=data["reason"])
    res = make_response(jsonify(order.as_json()), 200)
    res.headers["Content-Type"] = "application/json"
    res.headers["ETag"] = order.compute_etag()
    return res


# -----------------------------------------------------------------------------
# 7. REDIRECT ON SINGULAR NOUN (GET /order/<id>)
# -----------------------------------------------------------------------------
@app.route("/order/<order_id>", methods=["GET"])
def redirect_order(order_id: str):
    res = make_response("", 301)
    res.headers["Location"] = f"/orders/{order_id}"
    return res


# -----------------------------------------------------------------------------
# GLOBAL ERROR HANDLERS
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return problem(404, "Not Found", "Endpoint or resource not found.")


@app.errorhandler(405)
def method_not_allowed(e):
    res = problem(405, "Method Not Allowed", f"Method '{request.method}' not allowed.")
    res.headers["Allow"] = "GET, POST, OPTIONS, HEAD"
    return res


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
