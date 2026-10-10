from flask import Flask, request, jsonify, make_response, Response, g
import os

from models import Order, validate_order_payload, validate_update_payload, validate_cancellation_payload, is_valid_uuid
from store import store
from errors import problem
from client import payment_client, PaymentRefusedError, PaymentGatewayUnavailableError


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


def _is_json_like_accept(value: str) -> bool:
    if not value:
        return True
    for part in value.split(","):
        media = part.split(";", 1)[0].strip().lower()
        if media in ("application/json", "application/problem+json", "application/*", "*/*"):
            return True
    return False


def _accept_value(accept_header: str):
    if not accept_header:
        return "application/json"
    candidate = None
    best_q = -1.0
    for part in accept_header.split(","):
        item = part.strip()
        if not item:
            continue
        media = item.split(";", 1)[0].strip().lower()
        q = 1.0
        if ";" in item:
            for params in item.split(";")[1:]:
                if params.strip().lower().startswith("q="):
                    try:
                        q = float(params.split("=", 1)[1].strip())
                    except (ValueError, TypeError):
                        q = 1.0
        if q <= 0:
            continue
        if media == "application/xml":
            if q > best_q:
                candidate = "application/xml"
                best_q = q
        elif media in ("application/json", "application/problem+json"):
            if q > best_q:
                candidate = "application/json"
                best_q = q
        elif media in ("*/*", "application/*"):
            if q > best_q:
                candidate = "application/json"
                best_q = q
    return candidate or "application/json"


def _to_xml(value, tag_name="root"):
    if isinstance(value, dict):
        pieces = []
        for key, item in value.items():
            if item is None:
                pieces.append(f"<{key}></{key}>")
            else:
                pieces.append(f"<{key}>{_to_xml(item, key)}</{key}>")
        return "".join(pieces)
    if isinstance(value, list):
        items = "".join(f"<{tag_name}>{_to_xml(item, tag_name)}</{tag_name}>" for item in value)
        return items
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    escaped = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return escaped


def _render_payload(data, status=200, accept_header=None):
    negotiated = _accept_value(accept_header or request.headers.get("Accept") or "application/json")
    if negotiated == "application/xml":
        body = f"<response>{_to_xml(data)}</response>"
        return make_response(body, status, {"Content-Type": "application/xml; charset=utf-8"})
    payload = jsonify(data)
    payload.status_code = status
    payload.headers["Content-Type"] = "application/json; charset=utf-8"
    return payload


@app.before_request
def process_incoming_request():
    if request.method == "POST" and "X-HTTP-Method-Override" in request.headers:
        override = request.headers["X-HTTP-Method-Override"].upper()
        if override in ["PUT", "DELETE", "PATCH"]:
            request.environ["REQUEST_METHOD"] = override

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
            type_value="rate-limited",
            extra_headers={"Retry-After": str(retry_after)}
        )

    accept = request.headers.get("Accept")
    if accept and request.method not in ("OPTIONS", "HEAD"):
        chosen = _accept_value(accept)
        if not any(x in chosen for x in ["application/json", "application/xml"]) and not _is_json_like_accept(accept):
            return problem(
                406,
                "Not Acceptable",
                "Supported media types: application/json or application/xml.",
                type_value="unsupported-format"
            )

    if request.method in ("POST", "PUT", "DELETE") and request.path.endswith("/cancel"):
        auth = request.headers.get("Authorization", "").strip()
        if not auth.startswith("Bearer ") or not auth.replace("Bearer ", "").strip():
            return problem(
                status=401,
                title="Unauthorized",
                detail="Missing or empty Bearer token in Authorization header.",
                type_value="unauthorized",
                extra_headers={"WWW-Authenticate": 'Bearer realm="CampusEats Orders API"'}
            )

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
                type_value="unauthorized",
                extra_headers={"WWW-Authenticate": 'Bearer realm="CampusEats Orders API"'}
            )


@app.after_request
def add_response_headers(response: Response) -> Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Server"] = "CampusEats-OrdersService/2.0"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, If-None-Match, If-Match, Idempotency-Key, X-HTTP-Method-Override"
    response.headers["Access-Control-Expose-Headers"] = "Location, ETag, X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After"
    if hasattr(g, "rate_limit"):
        response.headers["X-RateLimit-Limit"] = str(g.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(g.rate_remaining)
    return response


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


@app.route("/orders", methods=["POST"])
def create_order():
    if request.mimetype not in ("application/json", "application/*+json", None):
        return problem(
            415,
            "Unsupported Media Type",
            "Request body must be application/json.",
            type_value="unsupported-media-type"
        )

    try:
        data = request.get_json(force=False, silent=False)
    except Exception as exc:
        return problem(400, "Bad Request", "Malformed JSON payload.", type_value="malformed-json", detail=str(exc))

    if data is None:
        return problem(400, "Bad Request", "Malformed JSON payload.", type_value="malformed-json")

    ok, summary, code, errors = validate_order_payload(data)
    if not ok:
        if errors:
            return problem(
                status=code,
                title="Validation Failed",
                detail=summary,
                type_value="validation-error" if code == 422 else "bad-request",
                errors=errors,
            )
        return problem(code, "Bad Request", summary, type_value="bad-request")

    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        cached = store.get_idempotency_record(idem_key)
        if cached:
            ordered = cached["body"]
            res = _render_payload(ordered, cached["status_code"], request.headers.get("Accept"))
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
        custom_notes=data.get("custom_notes"),
        address=data.get("address")
    )

    try:
        payment_client.charge(
            order_id=order.id,
            amount=order.total_price,
            customer_id=order.customer_id,
            payment_token=order.raw_payment_token,
            idempotency_key=idem_key,
        )
    except PaymentRefusedError as pe:
        return problem(
            422,
            "Payment Declined",
            pe.detail or "Payment was declined by the upstream payment service.",
            type_value="payment-declined",
            detail=pe.detail or "Payment was declined by the upstream payment service."
        )
    except PaymentGatewayUnavailableError as pge:
        return problem(
            503,
            "Service Unavailable",
            "Payment service is temporarily unavailable. Please retry later.",
            type_value="service-unavailable",
            extra_headers={"Retry-After": "5"}
        )

    rep = order.as_json()
    location = f"/orders/{order.id}"
    etag = order.compute_etag()

    store.save(order, idempotency_key=idem_key, cached_response={
        "body": rep,
        "status_code": 201,
        "location": location,
        "etag": etag,
    })

    res = _render_payload(rep, 201, request.headers.get("Accept"))
    res.headers["Location"] = location
    res.headers["ETag"] = etag
    return res


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.", type_value="bad-request")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.", type_value="order-not-found")

    current_etag = order.compute_etag()
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match:
        etags = [e.strip() for e in if_none_match.split(",")]
        if "*" in etags or current_etag in etags:
            res = make_response("", 304)
            res.headers["ETag"] = current_etag
            res.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
            return res

    res = _render_payload(order.as_json(), 200, request.headers.get("Accept"))
    res.headers["ETag"] = current_etag
    res.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
    return res


@app.route("/orders", methods=["GET"])
def list_orders():
    cust_id = request.args.get("customer_id")
    status = request.args.get("status")
    sort = request.args.get("sort", "ordered_at_desc")

    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 10))))
    except ValueError:
        return problem(400, "Bad Request", "page and limit must be integers.", type_value="bad-request")

    if cust_id and not is_valid_uuid(cust_id):
        return problem(400, "Bad Request", "customer_id must be a valid UUID.", type_value="bad-request")

    orders, total = store.list_all(customer_id=cust_id, status=status, sort_by=sort, page=page, limit=limit)
    payload = {
        "orders": [o.as_json() for o in orders],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
        },
    }
    res = _render_payload(payload, 200, request.headers.get("Accept"))
    res.headers["Cache-Control"] = "no-store"
    return res


@app.route("/orders/<order_id>", methods=["PUT"])
def update_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.", type_value="bad-request")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.", type_value="order-not-found")

    if_match = request.headers.get("If-Match")
    current_etag = order.compute_etag()
    if not if_match or (if_match != "*" and current_etag not in [e.strip() for e in if_match.split(",")]):
        return problem(412, "Precondition Failed", "If-Match ETag mismatch or missing.", type_value="precondition-failed")

    if order.status in ["delivered", "cancelled"]:
        return problem(409, "Illegal Transition", f"Cannot update order with status '{order.status}'.", type_value="illegal-transition")

    data = request.get_json(silent=True) or {}
    ok, summary, code, errors = validate_update_payload(data)
    if not ok:
        return problem(code, "Validation Failed", summary, type_value="validation-error", errors=errors)

    order.replace(data)
    new_etag = order.compute_etag()
    res = _render_payload(order.as_json(), 200, request.headers.get("Accept"))
    res.headers["ETag"] = new_etag
    return res


@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.", type_value="bad-request")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.", type_value="order-not-found")

    if order.status in ["preparing", "out_for_delivery", "delivered"]:
        return problem(409, "Illegal Transition", f"Cannot delete active order with status '{order.status}'.", type_value="illegal-transition")

    store.delete(order_id)
    return make_response("", 204)


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(400, "Bad Request", f"Invalid UUID: '{order_id}'.", type_value="bad-request")

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order '{order_id}' not found.", type_value="order-not-found")

    if order.status == "cancelled":
        return problem(409, "Illegal Transition", "Order is already cancelled.", type_value="illegal-transition")

    if order.status in ["delivered", "out_for_delivery"]:
        return problem(409, "Illegal Transition", f"Cannot cancel order in status '{order.status}'.", type_value="illegal-transition")

    data = request.get_json(silent=True) or {}
    ok, summary, code, errors = validate_cancellation_payload(data)
    if not ok:
        return problem(code, "Validation Failed", summary, type_value="validation-error", errors=errors)

    order.cancel(reason=data["reason"])
    res = _render_payload(order.as_json(), 200, request.headers.get("Accept"))
    res.headers["ETag"] = order.compute_etag()
    return res


@app.route("/order/<order_id>", methods=["GET"])
def redirect_order(order_id: str):
    res = make_response("", 301)
    res.headers["Location"] = f"/orders/{order_id}"
    return res


@app.errorhandler(404)
def not_found(e):
    return problem(404, "Not Found", "Endpoint or resource not found.", type_value="order-not-found")


@app.errorhandler(405)
def method_not_allowed(e):
    res = problem(405, "Method Not Allowed", f"Method '{request.method}' not allowed.", type_value="method-not-allowed")
    res.headers["Allow"] = "GET, POST, OPTIONS, HEAD"
    return res


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
