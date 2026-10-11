"""
CampusEats Orders Microservice (REST) — Honest Responses & Problem Details
CS 543 Web Services · Assignment 6
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra

Part A: Status Codes (Map every outcome, no 200 on failure, Location on 201, Retry-After on 429/503)
Part B: One Error Shape (RFC 7807/9457 Problem Details, stable type catalogue, 422 field errors, no internal leak)
Part C: Request Validation & Formats (POST /orders schema, multi-error collection, Accept content negotiation JSON/XML, charset=utf-8)
Part D: Live Verification & Proof Transcripts
"""

import os
import logging
from flask import Flask, request, jsonify, make_response, Response, g
from models import Order, orders_to_xml
from schema import (
    validate_create_order,
    validate_patch_order,
    validate_cancellation,
    is_valid_uuid
)
from store import store
from errors import problem
from client import (
    payment_client,
    PaymentRefusedError,
    PaymentGatewayUnavailableError,
    ItemUnavailableError
)

# Configure server-side logging (Internals logged server-side, never leaked to client)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("campuseats.orders")


# -----------------------------------------------------------------------------
# Method Override Middleware for constrained clients (A5 / A6)
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


def wants_xml_negotiation() -> bool:
    """Helper to detect if client requested XML representation."""
    accept = request.headers.get("Accept", "")
    return "application/xml" in accept or "text/xml" in accept


def format_order_response(order: Order, status_code: int = 200, extra_headers: dict = None) -> Response:
    """
    Renders an Order entity according to content negotiation (JSON or XML).
    Sets Content-Type with charset=utf-8.
    """
    if wants_xml_negotiation():
        res = make_response(order.to_xml(), status_code)
        res.headers["Content-Type"] = "application/xml; charset=utf-8"
    else:
        res = make_response(jsonify(order.as_json()), status_code)
        res.headers["Content-Type"] = "application/json; charset=utf-8"

    if extra_headers:
        for k, v in extra_headers.items():
            res.headers[k] = v
    return res


# -----------------------------------------------------------------------------
# REQUEST HOOKS: Method Override, Content Negotiation, Auth, Rate Limiting
# -----------------------------------------------------------------------------
@app.before_request
def process_incoming_request():
    # Method override support
    if request.method == "POST" and "X-HTTP-Method-Override" in request.headers:
        override = request.headers["X-HTTP-Method-Override"].upper()
        if override in ["PUT", "DELETE", "PATCH"]:
            request.environ["REQUEST_METHOD"] = override

    # Check simulated maintenance / service outage (Requirement A4 / B2)
    if store.is_outage() or request.headers.get("X-Simulate-Outage") == "1":
        return problem(
            status=503,
            title="Service Unavailable",
            detail="The CampusEats Orders Service is undergoing scheduled maintenance. Please retry shortly.",
            type_slug="service-unavailable",
            extra_headers={"Retry-After": "60"}
        )

    # Rate limiting check (Requirement A4: 429 with Retry-After)
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
            type_slug="rate-limit-exceeded",
            extra_headers={"Retry-After": str(retry_after)}
        )

    # Content negotiation check on Accept header (Requirement C3: 406 if unproducible)
    accept = request.headers.get("Accept")
    if accept and request.method != "OPTIONS":
        allowed_media_types = [
            "application/json",
            "application/problem+json",
            "application/xml",
            "text/xml",
            "application/problem+xml",
            "*/*",
            "application/*"
        ]
        if not any(m in accept for m in allowed_media_types):
            return problem(
                status=406,
                title="Not Acceptable",
                detail="Supported media types: application/json, application/xml.",
                type_slug="not-acceptable"
            )

    # Authorization check on state-mutating endpoints
    needs_auth = (
        (request.path == "/orders" and request.method == "POST") or
        (request.path.startswith("/orders/") and request.method in ["PUT", "PATCH", "DELETE"]) or
        request.path.endswith("/cancel")
    )
    if needs_auth:
        auth = request.headers.get("Authorization", "").strip()
        if not auth.startswith("Bearer ") or not auth.replace("Bearer ", "").strip():
            return problem(
                status=401,
                title="Unauthorized",
                detail="Missing or invalid Bearer token in Authorization header.",
                type_slug="unauthorized",
                extra_headers={"WWW-Authenticate": 'Bearer realm="CampusEats Orders API"'}
            )


@app.after_request
def add_response_headers(response: Response) -> Response:
    # Requirement C4: Explicit Content-Type with charset=utf-8 on every body
    ct = response.headers.get("Content-Type", "")
    if ct and "charset=" not in ct:
        if "application/json" in ct or "application/problem+json" in ct or "application/xml" in ct or "application/problem+xml" in ct or "text/xml" in ct:
            response.headers["Content-Type"] = f"{ct}; charset=utf-8"

    # Security & standard headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Server"] = "CampusEats-OrdersService/2.0"

    # CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, If-None-Match, If-Match, Idempotency-Key, X-HTTP-Method-Override, X-Simulate-Outage"
    response.headers["Access-Control-Expose-Headers"] = "Location, ETag, X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After"

    # Rate limit status
    if hasattr(g, "rate_limit"):
        response.headers["X-RateLimit-Limit"] = str(g.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(g.rate_remaining)

    return response


# -----------------------------------------------------------------------------
# OPTIONS HANDLERS
# -----------------------------------------------------------------------------
@app.route("/orders", methods=["OPTIONS"])
def options_orders():
    res = make_response("", 204)
    res.headers["Allow"] = "GET, POST, OPTIONS, HEAD"
    return res


@app.route("/orders/<order_id>", methods=["OPTIONS"])
def options_order_item(order_id: str):
    res = make_response("", 204)
    res.headers["Allow"] = "GET, PUT, PATCH, DELETE, OPTIONS, HEAD"
    return res


# -----------------------------------------------------------------------------
# 1. CREATE ORDER (POST /orders)
# -----------------------------------------------------------------------------
@app.route("/orders", methods=["POST"])
def create_order():
    # Enforce application/json request Content-Type
    if not request.is_json and request.content_length and request.content_length > 0:
        return problem(
            status=415,
            title="Unsupported Media Type",
            detail="Content-Type must be application/json.",
            type_slug="unsupported-media-type"
        )

    try:
        data = request.get_json()
    except Exception as e:
        logger.warning("JSON decode exception: %s", str(e))
        return problem(
            status=400,
            title="Bad Request",
            detail="Malformed JSON body syntax.",
            type_slug="invalid-json"
        )

    # Requirements C1 & C2: Validate payload before acting, collect all errors
    is_valid, validation_errors, type_slug = validate_create_order(data)
    if not is_valid:
        title = "Unprocessable Entity"
        return problem(
            status=422,
            title=title,
            detail="Request body failed validation checks. See 'errors' for field-level details.",
            type_slug=type_slug or "validation-error",
            errors=validation_errors
        )

    # Check inventory availability (Requirement B2: item-unavailable)
    try:
        payment_client.check_items_availability(data["items"])
    except ItemUnavailableError as iu:
        return problem(
            status=422,
            title="Item Unavailable",
            detail=iu.detail,
            type_slug=iu.type_slug
        )

    # Check Idempotency-Key
    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        cached = store.get_idempotency_record(idem_key)
        if cached:
            if wants_xml_negotiation():
                res = make_response(cached["xml_bytes"], cached["status_code"])
                res.headers["Content-Type"] = "application/xml; charset=utf-8"
            else:
                res = make_response(jsonify(cached["json_body"]), cached["status_code"])
                res.headers["Content-Type"] = "application/json; charset=utf-8"
            res.headers["Location"] = cached["location"]
            res.headers["ETag"] = cached["etag"]
            res.headers["X-Cache-Lookup"] = "HIT-IDEMPOTENT"
            return res

    order = Order(
        customer_id=data["customer_id"],
        canteen_id=data["canteen_id"],
        address=data["address"],
        items=data["items"],
        delivery_fee=data.get("delivery_fee", 30.00),
        payment_token=data.get("payment_token"),
        custom_notes=data.get("custom_notes")
    )

    # Process payment authorization (wrapped with B4: Don't leak internals)
    try:
        payment_client.charge(
            order_id=order.id,
            amount=order.total_price,
            customer_id=order.customer_id,
            payment_token=order.raw_payment_token,
            idempotency_key=idem_key
        )
    except PaymentRefusedError as pe:
        logger.info("Payment refused for order %s: %s", order.id, pe.detail)
        return problem(
            status=422,
            title="Payment Declined",
            detail=pe.detail,
            type_slug=pe.type_slug
        )
    except PaymentGatewayUnavailableError as pge:
        logger.warning("Payment gateway unavailable for order %s: %s", order.id, pge.detail)
        return problem(
            status=503,
            title="Service Unavailable",
            detail=pge.detail,
            type_slug=pge.type_slug,
            extra_headers={"Retry-After": str(pge.retry_after)}
        )
    except Exception as e:
        logger.exception("Unexpected upstream payment failure for order %s: %s", order.id, str(e))
        return problem(
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred while contacting payment services.",
            type_slug="internal-server-error"
        )

    # Persist order (wrapped with B4: Don't leak internals)
    try:
        location = f"/orders/{order.id}"
        etag = order.compute_etag()
        json_rep = order.as_json()
        xml_rep = order.to_xml()

        store.save(order, idempotency_key=idem_key, cached_response={
            "json_body": json_rep,
            "xml_bytes": xml_rep,
            "status_code": 201,
            "location": location,
            "etag": etag
        })
    except Exception as db_err:
        logger.exception("Database error while saving order %s: %s", order.id, str(db_err))
        return problem(
            status=500,
            title="Internal Server Error",
            detail="An internal storage failure occurred while recording the order.",
            type_slug="internal-server-error"
        )

    # Requirement A3: 201 Created with Location header pointing to new order
    return format_order_response(order, status_code=201, extra_headers={
        "Location": location,
        "ETag": etag
    })


# -----------------------------------------------------------------------------
# 2. READ SINGLE ORDER (GET /orders/<id>)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Order identifier '{order_id}' is not a valid UUID.",
            type_slug="validation-error"
        )

    try:
        order = store.get(order_id)
    except Exception as e:
        logger.exception("Internal store lookup error for order %s: %s", order_id, str(e))
        return problem(
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred while retrieving order.",
            type_slug="internal-server-error"
        )

    if not order:
        return problem(
            status=404,
            title="Not Found",
            detail=f"Order with ID '{order_id}' was not found in our records.",
            type_slug="order-not-found"
        )

    current_etag = order.compute_etag()

    # Conditional GET via If-None-Match -> 304 Not Modified
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match:
        etags = [e.strip() for e in if_none_match.split(",")]
        if "*" in etags or current_etag in etags:
            res = make_response("", 304)
            res.headers["ETag"] = current_etag
            res.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
            return res

    return format_order_response(order, status_code=200, extra_headers={
        "ETag": current_etag,
        "Cache-Control": "private, max-age=60, must-revalidate"
    })


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
        return problem(
            status=400,
            title="Bad Request",
            detail="Query parameters 'page' and 'limit' must be valid integers.",
            type_slug="validation-error"
        )

    if cust_id and not is_valid_uuid(cust_id):
        return problem(
            status=400,
            title="Bad Request",
            detail="Query parameter 'customer_id' must be a valid UUID format.",
            type_slug="validation-error"
        )

    valid_statuses = ["placed", "preparing", "ready_for_pickup", "out_for_delivery", "delivered", "cancelled"]
    if status and status not in valid_statuses:
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Query parameter 'status' must be one of: {', '.join(valid_statuses)}.",
            type_slug="validation-error"
        )

    try:
        orders, total = store.list_all(customer_id=cust_id, status=status, sort_by=sort, page=page, limit=limit)
    except Exception as e:
        logger.exception("Store list query error: %s", str(e))
        return problem(
            status=500,
            title="Internal Server Error",
            detail="An error occurred querying order records.",
            type_slug="internal-server-error"
        )

    pagination = {"total": total, "page": page, "limit": limit}

    if wants_xml_negotiation():
        xml_bytes = orders_to_xml(orders, pagination)
        res = make_response(xml_bytes, 200)
        res.headers["Content-Type"] = "application/xml; charset=utf-8"
    else:
        res = make_response(jsonify({
            "orders": [o.as_json() for o in orders],
            "pagination": pagination
        }), 200)
        res.headers["Content-Type"] = "application/json; charset=utf-8"

    res.headers["Cache-Control"] = "no-store"
    return res


# -----------------------------------------------------------------------------
# 4. PARTIAL UPDATE (PATCH /orders/<id>) — Requirement A1
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["PATCH"])
def patch_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Order identifier '{order_id}' is not a valid UUID.",
            type_slug="validation-error"
        )

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            title="Not Found",
            detail=f"Order '{order_id}' not found.",
            type_slug="order-not-found"
        )

    # State transition check (Requirement B2: illegal-transition)
    if order.status in ["delivered", "cancelled"]:
        return problem(
            status=409,
            title="State Conflict",
            detail=f"Cannot patch order in terminal state '{order.status}'.",
            type_slug="illegal-transition"
        )

    # Optional optimistic concurrency check on PATCH
    if_match = request.headers.get("If-Match")
    current_etag = order.compute_etag()
    if if_match and (if_match != "*" and current_etag not in [e.strip() for e in if_match.split(",")]):
        return problem(
            status=412,
            title="Precondition Failed",
            detail="If-Match ETag mismatch.",
            type_slug="precondition-failed"
        )

    if not request.is_json:
        return problem(
            status=415,
            title="Unsupported Media Type",
            detail="Content-Type must be application/json.",
            type_slug="unsupported-media-type"
        )

    try:
        data = request.get_json()
    except Exception:
        return problem(
            status=400,
            title="Bad Request",
            detail="Malformed JSON body syntax.",
            type_slug="invalid-json"
        )

    is_valid, validation_errors = validate_patch_order(data)
    if not is_valid:
        return problem(
            status=422,
            title="Unprocessable Entity",
            detail="PATCH payload validation failed.",
            type_slug="validation-error",
            errors=validation_errors
        )

    # Check inventory if items are being updated
    if "items" in data:
        try:
            payment_client.check_items_availability(data["items"])
        except ItemUnavailableError as iu:
            return problem(
                status=422,
                title="Item Unavailable",
                detail=iu.detail,
                type_slug=iu.type_slug
            )

    order.patch(data)
    new_etag = order.compute_etag()

    return format_order_response(order, status_code=200, extra_headers={"ETag": new_etag})


# -----------------------------------------------------------------------------
# 5. FULL REPLACEMENT (PUT /orders/<id>)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["PUT"])
def update_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Order identifier '{order_id}' is not a valid UUID.",
            type_slug="validation-error"
        )

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            title="Not Found",
            detail=f"Order '{order_id}' not found.",
            type_slug="order-not-found"
        )

    # Concurrency check (If-Match mandatory for PUT)
    if_match = request.headers.get("If-Match")
    current_etag = order.compute_etag()

    if not if_match or (if_match != "*" and current_etag not in [e.strip() for e in if_match.split(",")]):
        return problem(
            status=412,
            title="Precondition Failed",
            detail="If-Match header is mandatory for PUT and must match current resource ETag.",
            type_slug="precondition-failed"
        )

    if order.status in ["delivered", "cancelled"]:
        return problem(
            status=409,
            title="State Conflict",
            detail=f"Cannot update order in terminal state '{order.status}'.",
            type_slug="illegal-transition"
        )

    data = request.get_json(silent=True) or {}
    is_valid, validation_errors = validate_patch_order(data)
    if not is_valid:
        return problem(
            status=422,
            title="Unprocessable Entity",
            detail="Update payload validation failed.",
            type_slug="validation-error",
            errors=validation_errors
        )

    order.replace(data)
    new_etag = order.compute_etag()

    return format_order_response(order, status_code=200, extra_headers={"ETag": new_etag})


# -----------------------------------------------------------------------------
# 6. DELETE ORDER (DELETE /orders/<id>) — Requirement A1
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Invalid UUID: '{order_id}'.",
            type_slug="validation-error"
        )

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            title="Not Found",
            detail=f"Order '{order_id}' not found.",
            type_slug="order-not-found"
        )

    # State transition rule (Requirement B2: illegal-transition)
    if order.status in ["preparing", "ready_for_pickup", "out_for_delivery", "delivered"]:
        return problem(
            status=409,
            title="State Conflict",
            detail=f"Cannot delete active order with status '{order.status}'. Only placed or cancelled orders can be purged.",
            type_slug="illegal-transition"
        )

    store.delete(order_id)
    return make_response("", 204)


# -----------------------------------------------------------------------------
# 7. CANCEL ORDER (POST /orders/<id>/cancel)
# -----------------------------------------------------------------------------
@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    if not is_valid_uuid(order_id):
        return problem(
            status=400,
            title="Bad Request",
            detail=f"Invalid UUID: '{order_id}'.",
            type_slug="validation-error"
        )

    order = store.get(order_id)
    if not order:
        return problem(
            status=404,
            title="Not Found",
            detail=f"Order '{order_id}' not found.",
            type_slug="order-not-found"
        )

    # Illegal transition checks
    if order.status == "cancelled":
        return problem(
            status=409,
            title="State Conflict",
            detail="Order is already cancelled.",
            type_slug="illegal-transition"
        )

    if order.status in ["delivered", "out_for_delivery"]:
        return problem(
            status=409,
            title="State Conflict",
            detail=f"Cannot cancel order in status '{order.status}'. Food is already in transit or delivered.",
            type_slug="illegal-transition"
        )

    data = request.get_json(silent=True) or {}
    is_valid, validation_errors = validate_cancellation(data)
    if not is_valid:
        return problem(
            status=422,
            title="Unprocessable Entity",
            detail="Cancellation validation failed.",
            type_slug="validation-error",
            errors=validation_errors
        )

    order.cancel(reason=data["reason"])
    new_etag = order.compute_etag()

    return format_order_response(order, status_code=200, extra_headers={"ETag": new_etag})


# -----------------------------------------------------------------------------
# 8. SINGULAR NOUN REDIRECTION (GET /order/<id>)
# -----------------------------------------------------------------------------
@app.route("/order/<order_id>", methods=["GET"])
def redirect_order(order_id: str):
    res = make_response("", 301)
    res.headers["Location"] = f"/orders/{order_id}"
    return res


# -----------------------------------------------------------------------------
# GLOBAL ERROR HANDLERS (Requirement B1 & B4)
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return problem(
        status=404,
        title="Not Found",
        detail="The requested URL endpoint or resource does not exist on this server.",
        type_slug="order-not-found"
    )


@app.errorhandler(405)
def method_not_allowed(e):
    res = problem(
        status=405,
        title="Method Not Allowed",
        detail=f"HTTP method '{request.method}' is not supported for this endpoint.",
        type_slug="method-not-allowed"
    )
    res.headers["Allow"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
    return res


@app.errorhandler(Exception)
def unhandled_server_exception(e):
    # Requirement B4: Don't leak internals. Log server-side, return clean Problem Details
    logger.exception("Unhandled server exception: %s", str(e))
    return problem(
        status=500,
        title="Internal Server Error",
        detail="An internal server error occurred while processing the request. Our engineering team has been notified.",
        type_slug="internal-server-error"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5066))
    app.run(host="0.0.0.0", port=port, debug=False)
