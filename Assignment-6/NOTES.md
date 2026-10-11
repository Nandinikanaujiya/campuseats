# CS 543 Web Services · Assignment 6
## Honest Responses: Status Codes, Errors & Validation

### 👥 Team & Members (Team No. 11)
* **Nandini Kanaujiya** — `20251651061`
* **Radhika Verma** — `20251651075`
* **Alka Jha** — `20251651013`
* **Alok Mishra** — `20251651014`

---

## 1. Status Map

Every endpoint implemented in the CampusEats Orders Microservice, its canonical success status code, and the exact HTTP status code for each real failure scenario, with a one-line explanation of why each is returned:

| HTTP Method & Endpoint | Status Code | Outcome Category | One-Line Rationale |
|---|---|---|---|
| `POST /orders` | `201 Created` | Success | Order resource successfully created, payment authorized, and `Location: /orders/{id}` set. |
| `POST /orders` | `400 Bad Request` | Failure | Request body has malformed JSON syntax that cannot be parsed by the JSON decoder. |
| `POST /orders` | `401 Unauthorized` | Failure | Missing or empty Bearer token in the `Authorization` header (`WWW-Authenticate` issued). |
| `POST /orders` | `406 Not Acceptable` | Failure | The client requested a media format via `Accept` that the service cannot produce. |
| `POST /orders` | `415 Unsupported Media Type` | Failure | Request body was submitted without `Content-Type: application/json`. |
| `POST /orders` | `422 Unprocessable Entity` | Failure | Semantic validation failure (empty cart, qty $\le 0$, missing address, item unavailable, or card declined). |
| `POST /orders` | `429 Too Many Requests` | Failure | Client exceeded the rate quota (60 req/min); includes `Retry-After` header. |
| `POST /orders` | `500 Internal Server Error` | Failure | Unhandled database or system exception; details logged internally and masked from client. |
| `POST /orders` | `503 Service Unavailable` | Failure | Upstream payment gateway outage or simulated maintenance; includes `Retry-After: 30`. |
| `GET /orders/{id}` | `200 OK` | Success | Order found and full representation returned matching negotiated format (JSON/XML). |
| `GET /orders/{id}` | `304 Not Modified` | Success / Cache | Conditional GET: client `If-None-Match` matches current resource `ETag`; payload omitted. |
| `GET /orders/{id}` | `400 Bad Request` | Failure | Provided `order_id` in path is not a syntactically valid RFC 4122 UUID. |
| `GET /orders/{id}` | `404 Not Found` | Failure | No order entity exists in the store corresponding to the requested UUID (`order-not-found`). |
| `GET /orders/{id}` | `406 Not Acceptable` | Failure | Client requested unsupported MIME type in `Accept` header (e.g., `text/csv`). |
| `GET /orders/{id}` | `429 Too Many Requests` | Failure | Client exceeded rate quota for order reads; includes `Retry-After`. |
| `GET /orders/{id}` | `500 Internal Server Error` | Failure | Storage lookup failed due to unexpected internal persistence error. |
| `GET /orders` | `200 OK` | Success | Returns paginated, sorted, and filtered catalogue of orders matching query parameters. |
| `GET /orders` | `400 Bad Request` | Failure | Malformed query parameter (non-integer `page`/`limit`, invalid UUID `customer_id`, bad `status`). |
| `GET /orders` | `406 Not Acceptable` | Failure | Media type in `Accept` header is not supported by the collection resource. |
| `GET /orders` | `429 Too Many Requests` | Failure | Read rate limit exhausted across collection queries; includes `Retry-After`. |
| `PATCH /orders/{id}` | `200 OK` | Success | Order attributes partially modified, version incremented, new `ETag` assigned. |
| `PATCH /orders/{id}` | `400 Bad Request` | Failure | Malformed JSON syntax or invalid UUID in URL path. |
| `PATCH /orders/{id}` | `401 Unauthorized` | Failure | Modification attempted without valid Bearer authentication credentials. |
| `PATCH /orders/{id}` | `404 Not Found` | Failure | Targeted order does not exist in the repository. |
| `PATCH /orders/{id}` | `409 Conflict` | Failure | Lifecycle violation: order is in terminal state (`delivered` or `cancelled`) and cannot be patched. |
| `PATCH /orders/{id}` | `412 Precondition Failed` | Failure | Provided `If-Match` header does not match the resource's current ETag. |
| `PATCH /orders/{id}` | `415 Unsupported Media Type` | Failure | Payload supplied without `Content-Type: application/json`. |
| `PATCH /orders/{id}` | `422 Unprocessable Entity` | Failure | Attempted to modify forbidden fields or provided invalid attribute values (e.g., empty address). |
| `PATCH /orders/{id}` | `429 Too Many Requests` | Failure | Mutation rate limit exceeded; includes `Retry-After`. |
| `PUT /orders/{id}` | `200 OK` | Success | Order completely replaced with new editable state, version incremented, new ETag generated. |
| `PUT /orders/{id}` | `400 Bad Request` | Failure | Malformed JSON or invalid path UUID. |
| `PUT /orders/{id}` | `401 Unauthorized` | Failure | Unauthenticated caller attempted full resource replacement. |
| `PUT /orders/{id}` | `404 Not Found` | Failure | Order to replace does not exist in store. |
| `PUT /orders/{id}` | `409 Conflict` | Failure | Order has already reached terminal status (`delivered` or `cancelled`). |
| `PUT /orders/{id}` | `412 Precondition Failed` | Failure | `If-Match` header was missing or differed from the active resource ETag (lost update prevention). |
| `PUT /orders/{id}` | `415 Unsupported Media Type` | Failure | Request body submitted without `Content-Type: application/json`. |
| `PUT /orders/{id}` | `422 Unprocessable Entity` | Failure | Replacement payload failed schema validation (e.g., negative price or missing fields). |
| `PUT /orders/{id}` | `429 Too Many Requests` | Failure | Write rate quota exhausted; includes `Retry-After`. |
| `DELETE /orders/{id}` | `204 No Content` | Success | Order purged from repository; returns empty response body without entity data. |
| `DELETE /orders/{id}` | `400 Bad Request` | Failure | Path identifier is not a valid UUID string. |
| `DELETE /orders/{id}` | `401 Unauthorized` | Failure | Delete requested without Bearer token. |
| `DELETE /orders/{id}` | `404 Not Found` | Failure | Targeted order does not exist to be deleted. |
| `DELETE /orders/{id}` | `409 Conflict` | Failure | Business rule violation: active orders (`preparing`, `out_for_delivery`, `delivered`) cannot be deleted. |
| `DELETE /orders/{id}` | `429 Too Many Requests` | Failure | Deletion rate limit exhausted; includes `Retry-After`. |
| `POST /orders/{id}/cancel` | `200 OK` | Success | Order lifecycle transitioned to `cancelled`, reason recorded, and new ETag generated. |
| `POST /orders/{id}/cancel` | `400 Bad Request` | Failure | Invalid path UUID or malformed JSON. |
| `POST /orders/{id}/cancel` | `401 Unauthorized` | Failure | Caller attempted cancellation without valid Bearer authorization. |
| `POST /orders/{id}/cancel` | `404 Not Found` | Failure | Order not found to cancel. |
| `POST /orders/{id}/cancel` | `409 Conflict` | Failure | Illegal transition: order already cancelled or already in delivery/delivered (`illegal-transition`). |
| `POST /orders/{id}/cancel` | `422 Unprocessable Entity` | Failure | Cancellation reason missing or shorter than minimum required length (3 characters). |
| `OPTIONS /orders` | `204 No Content` | Success | Returns `Allow: GET, POST, OPTIONS, HEAD` headers for collection discovery. |
| `OPTIONS /orders/{id}` | `204 No Content` | Success | Returns `Allow: GET, PUT, PATCH, DELETE, OPTIONS, HEAD` headers for item verb discovery. |
| `GET /order/{id}` | `301 Moved Permanently` | Redirect | Singular noun URL redirects callers to the canonical plural `/orders/{id}` route. |

> **Anti-Pattern Guarantee (Requirement A2):** The service **never** returns `200 OK` with a failure body (such as `{ "ok": false }` or `{ "status": "error" }`). The HTTP status code **is** the result.

---

## 2. Type Catalogue

The service standardises on RFC 7807 / RFC 9457 Problem Details. All error responses share a stable URI type identifier rooted at `https://campuseats.internal/errors/<slug>`:

| Stable Type String (`slug`) | Complete RFC 7807 Type URI | What Triggers It |
|---|---|---|
| `empty-cart` | `https://campuseats.internal/errors/empty-cart` | Placing an order where the `items` array is empty (`[]`). |
| `item-unavailable` | `https://campuseats.internal/errors/item-unavailable` | One or more items in the order are out of stock or unavailable at the canteen. |
| `payment-declined` | `https://campuseats.internal/errors/payment-declined` | Upstream payment gateway refuses payment authorization (e.g. card declined, insufficient funds). |
| `order-not-found` | `https://campuseats.internal/errors/order-not-found` | A lookup, update, delete, or action references an order UUID that does not exist in storage. |
| `illegal-transition` | `https://campuseats.internal/errors/illegal-transition` | An action violates the order lifecycle state machine (e.g., cancelling an already cancelled order, updating a delivered order, or deleting an active kitchen order). |
| `validation-error` | `https://campuseats.internal/errors/validation-error` | Request payload fails structural schema validation (e.g., quantity $\le 0$, missing address, invalid UUIDs). Includes an `errors[]` array. |
| `invalid-json` | `https://campuseats.internal/errors/invalid-json` | Request payload body has syntax errors and cannot be parsed as valid JSON. |
| `unauthorized` | `https://campuseats.internal/errors/unauthorized` | Protected endpoint accessed without a Bearer authentication token in the `Authorization` header. |
| `not-acceptable` | `https://campuseats.internal/errors/not-acceptable` | Client `Accept` header demands a MIME representation that cannot be produced (e.g., `text/csv`). |
| `unsupported-media-type` | `https://campuseats.internal/errors/unsupported-media-type` | Client submitted a non-JSON body without `Content-Type: application/json`. |
| `precondition-failed` | `https://campuseats.internal/errors/precondition-failed` | Optimistic locking violation: `If-Match` header is missing on PUT or fails to match the active ETag. |
| `rate-limit-exceeded` | `https://campuseats.internal/errors/rate-limit-exceeded` | Client exceeded the 60 requests/minute sliding window threshold. Returns `Retry-After` header. |
| `service-unavailable` | `https://campuseats.internal/errors/service-unavailable` | Upstream service or gateway is temporarily down or undergoing maintenance. Returns `Retry-After: 30` or `60`. |
| `internal-server-error` | `https://campuseats.internal/errors/internal-server-error` | Unexpected internal runtime or persistence failure. Clean error returned while raw stack traces are logged server-side. |

---

## 3. Sample Problem Details Body & Field Labels

Below is a live Problem Details response returned by the CampusEats Orders Service when a client requests an order that does not exist (`GET /orders/3fa85f64-5717-4562-b3fc-2c963f66afa6`):

```http
HTTP/1.1 404 NOT FOUND
Server: CampusEats-OrdersService/2.0
Date: Sun, 11 Oct 2026 08:52:12 GMT
Content-Type: application/problem+json; charset=utf-8
Content-Length: 227
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
Access-Control-Allow-Origin: *
Connection: close

{
  "type": "https://campuseats.internal/errors/order-not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Order with ID '3fa85f64-5717-4562-b3fc-2c963f66afa6' was not found in our records.",
  "instance": "/orders/3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

### Field Breakdown & Annotations:
* **`type`** (`URI reference`):
  Identifies the specific problem type according to RFC 7807 §3.1. Clients can programmatically match on this stable URI (`.../errors/order-not-found`) rather than relying on brittle string matching of the human-readable text.
* **`title`** (`string`):
  A short, human-readable summary of the problem type (matches the standard HTTP status phrase "Not Found"). It does NOT vary between occurrences of the problem.
* **`status`** (`integer`):
  The HTTP status code generated by the origin server for this occurrence of the problem (`404`). It matches the HTTP response status line.
* **`detail`** (`string`):
  A human-readable explanation specific to this particular occurrence of the problem, giving the caller actionable context without leaking server implementation details.
* **`instance`** (`URI reference`):
  Identifies the specific resource URI where the failure took place (`/orders/3fa85f64-5717-4562-b3fc-2c963f66afa6`).

---

## 4. Field-Level 422 Reporting Multiple Bad Fields Simultaneously

When a client submits an invalid order creation body, the validator validates all fields before taking any action. Rather than failing fast on the first syntax or domain violation, it aggregates all errors into an `errors[]` array and responds with `422 Unprocessable Entity`.

### Live curl Request:
```bash
curl -i -X POST http://127.0.0.1:5066/orders \
  -H "Authorization: Bearer test-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3",
    "canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb",
    "address": "",
    "items": [
      {
        "menu_item_id": "1e84ceb4-e952-47f6-b0f1-136805a9f5a6",
        "item_name": "Chole Bhature",
        "quantity": 0,
        "unit_price": 90.0
      }
    ]
  }'
```

### Live 422 Response:
```http
HTTP/1.1 422 UNPROCESSABLE ENTITY
Server: CampusEats-OrdersService/2.0
Date: Sun, 11 Oct 2026 08:52:11 GMT
Content-Type: application/problem+json; charset=utf-8
Content-Length: 377
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
Access-Control-Allow-Origin: *
Connection: close

{
  "errors": [
    {
      "field": "address",
      "message": "Delivery address cannot be empty or whitespace only."
    },
    {
      "field": "items[0].quantity",
      "message": "Quantity must be an integer >= 1."
    }
  ],
  "detail": "Request body failed validation checks. See 'errors' for field-level details.",
  "instance": "/orders",
  "status": 422,
  "title": "Unprocessable Entity",
  "type": "https://campuseats.internal/errors/validation-error"
}
```

Both defective fields (`address` empty and `items[0].quantity` $\le 0$) are reported in a single turn, saving round-trips and allowing the client UI to highlight every invalid input simultaneously.

---

## 5. Safe Retries & Retry-After Semantics

### Naturally Retry-Safe Endpoints
In REST, operations that are **safe** (read-only, no state change) or **idempotent** (repeating produces identical side effects) are safe to retry across network drops:
1. `GET /orders` — Safe & idempotent. Re-reading catalogue causes zero side effects.
2. `GET /orders/{id}` — Safe & idempotent. Re-reading an order representation mutates nothing.
3. `OPTIONS /orders` and `OPTIONS /orders/{id}` — Safe & idempotent verb discovery.
4. `PUT /orders/{id}` — Idempotent. Re-submitting the same replacement state produces the same end state (protected by `If-Match`).
5. `DELETE /orders/{id}` — Idempotent. Once deleted, subsequent deletes leave the resource deleted (or return 404).

### Conditionally Retry-Safe Endpoint: `POST /orders`
By default, `POST` is neither safe nor idempotent (retrying an order creation could double-charge credit cards and create duplicate canteen orders).
* **CampusEats solution:** `POST /orders` is made retry-safe via the **`Idempotency-Key`** header. When a client supplies an `Idempotency-Key: <UUID>`, the service caches the initial transaction and returns the cached `201 Created` with `X-Cache-Lookup: HIT-IDEMPOTENT` on subsequent replays.

### Status Codes Telling a Client to Retry
Only **transient failures** indicate that retrying may succeed:
* **`429 Too Many Requests`**: Client exceeded rate limits. Must back off for the duration specified in the **`Retry-After`** header (e.g., `Retry-After: 48`).
* **`503 Service Unavailable`**: Service or upstream gateway is temporarily overloaded or undergoing maintenance. The **`Retry-After`** header signals the wait time (e.g., `Retry-After: 30` or `Retry-After: 60`).
* **`502 Bad Gateway` / `504 Gateway Timeout`**: Upstream transient network or gateway failure. Can be retried with exponential backoff and jitter.

> **Crucial Rule:** Clients must **NEVER retry a 4xx error unchanged** (such as `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, or `422 Unprocessable Entity`). Without modifying the request payload or credentials, re-sending will reliably produce the exact same failure.

---

## 6. Mapping Internal Errors to Clean Client Errors (B4: Don't Leak Internals)

### Architecture of Error Sanitization
In CampusEats, risky boundaries (database persistence, external payment gateway communication, and unhandled system exceptions) are wrapped in `try/catch` blocks.
* Detailed debugging traces, raw database error messages, and network callouts are logged **server-side** via Python's standard `logging` library.
* The client receives a clean, standardized **`500 Internal Server Error`** Problem Details response with zero leaked implementation artifacts.

### Concrete Example from `app.py`:

```python
# Server-side implementation:
try:
    payment_client.charge(
        order_id=order.id,
        amount=order.total_price,
        customer_id=order.customer_id,
        payment_token=order.raw_payment_token,
        idempotency_key=idem_key
    )
except Exception as e:
    # 1. Log full internal exception server-side
    logger.exception("Unexpected upstream payment failure for order %s: %s", order.id, str(e))
    # 2. Return clean, sanitized Problem Details to client
    return problem(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred while contacting payment services.",
        type_slug="internal-server-error"
    )
```

### What We Hide From the Caller:
1. **Raw Database Exceptions & SQL Queries:**
   * *Hidden:* `psycopg2.OperationalError: connection to server at "10.0.4.12", port 5432 failed: FATAL: password authentication failed for user "canteen_app"`
   * *Client sees:* `"detail": "An internal storage failure occurred while recording the order."`
2. **Internal Architecture & Infrastructure IPs:**
   * *Hidden:* Internal hostnames, private IPs (`10.0.4.12`), port numbers, or upstream payment gateway cluster endpoints (`https://gateway-internal.prod.aws.campuseats.corp/v1/charge`).
3. **Source Code Paths & Stack Traces:**
   * *Hidden:* File paths (`C:\AI Coding Challenge Platform\Assignment-6\client.py:98`), function names, and line numbers that malicious callers could use to map software vulnerabilities.

---

## 7. Content Negotiation: Same Order as JSON and XML

The service inspects the client's HTTP `Accept` header and produces the appropriate MIME representation, setting `Content-Type: <media-type>; charset=utf-8` on each response.

### 7.1. Order Representation as JSON

#### Client Request with `Accept: application/json`:
```http
GET /orders/99b6a144-24aa-40c2-b268-6f04dcd3bbc2 HTTP/1.1
Host: 127.0.0.1:5066
Accept: application/json
```

#### Server Response:
```http
HTTP/1.1 200 OK
Server: CampusEats-OrdersService/2.0
Date: Sun, 11 Oct 2026 08:52:12 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 647
ETag: "ec2f1f44a3311687f8d42d3c92e92c24"
Cache-Control: private, max-age=60, must-revalidate
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
Access-Control-Allow-Origin: *
Connection: close

{
  "id": "99b6a144-24aa-40c2-b268-6f04dcd3bbc2",
  "customer_id": "d1e2f3a4-b5c6-47d8-9e0f-1a2b3c4d5e6f",
  "canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb",
  "address": "Faculty Residence Block B, Flat 104",
  "status": "placed",
  "subtotal": 80.0,
  "service_fee": 15.0,
  "delivery_fee": 30.0,
  "tax": 4.0,
  "total_price": 129.0,
  "version": 1,
  "ordered_at": "2026-10-11T08:52:12.756281+00:00",
  "updated_at": "2026-10-11T08:52:12.756281+00:00",
  "cancelled_at": null,
  "cancellation_reason": null,
  "items": [
    {
      "menu_item_id": "2f95dfc5-f063-4807-c102-247916b0a6b7",
      "item_name": "Masala Dosa with Sambar",
      "quantity": 1,
      "unit_price": 80.0
    }
  ]
}
```

---

### 7.2. Same Order Representation as XML

#### Client Request with `Accept: application/xml`:
```http
GET /orders/99b6a144-24aa-40c2-b268-6f04dcd3bbc2 HTTP/1.1
Host: 127.0.0.1:5066
Accept: application/xml
```

#### Server Response:
```http
HTTP/1.1 200 OK
Server: CampusEats-OrdersService/2.0
Date: Sun, 11 Oct 2026 08:52:12 GMT
Content-Type: application/xml; charset=utf-8
Content-Length: 686
ETag: "ec2f1f44a3311687f8d42d3c92e92c24"
Cache-Control: private, max-age=60, must-revalidate
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
Access-Control-Allow-Origin: *
Connection: close

<?xml version='1.0' encoding='utf-8'?>
<order>
  <id>99b6a144-24aa-40c2-b268-6f04dcd3bbc2</id>
  <customer_id>d1e2f3a4-b5c6-47d8-9e0f-1a2b3c4d5e6f</customer_id>
  <canteen_id>b38ad05b-816e-4e22-b7c9-2b83c64fb9cb</canteen_id>
  <address>Faculty Residence Block B, Flat 104</address>
  <status>placed</status>
  <subtotal>80.00</subtotal>
  <service_fee>15.00</service_fee>
  <delivery_fee>30.00</delivery_fee>
  <tax>4.00</tax>
  <total_price>129.00</total_price>
  <version>1</version>
  <ordered_at>2026-10-11T08:52:12.756281+00:00</ordered_at>
  <updated_at>2026-10-11T08:52:12.756281+00:00</updated_at>
  <items>
    <item>
      <menu_item_id>2f95dfc5-f063-4807-c102-247916b0a6b7</menu_item_id>
      <item_name>Masala Dosa with Sambar</item_name>
      <quantity>1</quantity>
      <unit_price>80.00</unit_price>
    </item>
  </items>
</order>
```

---

### 7.3. Negotiation Rejection (`406 Not Acceptable`)

If the client requests an unsupported media type (e.g. `Accept: text/csv`):

```http
GET /orders/99b6a144-24aa-40c2-b268-6f04dcd3bbc2 HTTP/1.1
Host: 127.0.0.1:5066
Accept: text/csv
```

#### Server Response:
```http
HTTP/1.1 406 NOT ACCEPTABLE
Server: CampusEats-OrdersService/2.0
Date: Sun, 11 Oct 2026 08:52:12 GMT
Content-Type: application/problem+json; charset=utf-8
Content-Length: 191
Connection: close

{
  "detail": "Supported media types: application/json, application/xml.",
  "instance": "/orders/99b6a144-24aa-40c2-b268-6f04dcd3bbc2",
  "status": 406,
  "title": "Not Acceptable",
  "type": "https://campuseats.internal/errors/not-acceptable"
}
```
