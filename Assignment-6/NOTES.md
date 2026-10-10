# Assignment 6 Notes

The original Assignment 5 implementation remains in `Assignment-5/` and is intentionally untouched. This directory contains the Assignment 6 extension.

## 1. Status map
- `POST /orders` -> success `201 Created`; failure `400` malformed JSON, `415` unsupported media type, `422` validation errors, `401` missing auth, `429` rate limit, `503` payment service unavailable.
- `GET /orders/{order_id}` -> success `200 OK`; failure `400` invalid UUID, `404` order not found, `406` unsupported Accept format, `304` not modified when ETag matches.
- `GET /orders` -> success `200 OK`; failure `400` invalid query params, `406` unsupported Accept format, `429` rate limit.
- `PUT /orders/{order_id}` -> success `200 OK`; failure `400` invalid id or body, `401` missing auth, `404` order missing, `409` illegal transition, `412` stale If-Match, `422` field validation failure.
- `DELETE /orders/{order_id}` -> success `204 No Content`; failure `400` invalid UUID, `401` missing auth, `404` order missing, `409` illegal transition.
- `POST /orders/{order_id}/cancel` -> success `200 OK`; failure `400` invalid reason, `401` missing auth, `404` order missing, `409` illegal transition.

## 2. Stable error type catalogue
- `empty-cart` -> when `items` is an empty array; trigger: create/update order with no items.
- `item-unavailable` -> when an upstream stock lookup rejects an item; trigger: item not in inventory / unavailable.
- `payment-declined` -> when upstream payment service refuses the charge.
- `order-not-found` -> when the requested order id does not exist.
- `illegal-transition` -> when an order status change violates the state machine.
- `validation-error` -> field-level validation failure.
- `malformed-json` -> JSON syntax/parse error.
- `unsupported-format` -> Accept or media type unsupported.
- `rate-limited` -> request exceeds rate limit.
- `precondition-failed` -> stale or missing If-Match ETag.
- `service-unavailable` -> upstream payment or dependency temporarily unavailable.

## 3. One Problem Details body
```json
{
  "type": "https://campuseats.internal/problems/empty-cart",
  "title": "Validation Failed",
  "status": 422,
  "detail": "Order items must not be empty.",
  "errors": [
    {"field": "items", "message": "must contain at least one item"}
  ]
}
```
Field meanings:
- `type`: stable machine-readable identifier
- `title`: short human text
- `status`: HTTP status code
- `detail`: summary of what went wrong
- `errors`: field-level invalid fields and reasons

## 4. Example field-level 422 response with two bad fields
```json
{
  "type": "https://campuseats.internal/problems/validation-error",
  "title": "Validation Failed",
  "status": 422,
  "detail": "Request validation failed.",
  "errors": [
    {"field": "items[0].quantity", "message": "must be an integer >= 1"},
    {"field": "address", "message": "is required and must not be blank"}
  ]
}
```

## 5. Retry-safe endpoints and status codes
Safe retry behavior is only for transient failures and only when the request is unchanged:
- `GET /orders/{order_id}` and `GET /orders` are safe to retry: `200`, `304`, `404` when not found if the read is retried.
- `POST /orders` is retry-safe only with the same `Idempotency-Key`; repeated identical calls do not duplicate the order or payment.
- `429 Too Many Requests` and `503 Service Unavailable` should include `Retry-After`; clients should wait and retry later.
- `4xx` errors like `400`, `401`, `404`, `409`, `412`, `422` are not automatically safe to retry unless the request semantics are explicitly repeated with the same idempotency key or the operation is known safe.

## 6. Internal-error mapping
The service wraps risky operations in `try/except`. Example: payment failures are caught and mapped to a clean client-facing error. In `Assignment-6/app.py` the payment charge is wrapped; the details are hidden from the caller and replaced with a safe message such as `Payment Declined` or `Service Unavailable`.
The server logs the technical detail internally, but the response does not leak stack traces, raw database messages, gateways, or secrets.

## 7. JSON and XML examples with Accept headers
If supported by the client, JSON is returned by default. XML is selected when the request says `Accept: application/xml`.

JSON example:
```http
Accept: application/json
```
```json
{
  "id": "e7a0a0fe-1e0d-4f43-9b3d-2b2b356d8fd7",
  "customer_id": "0d37cfab-4f9c-4eb8-b2d4-bd0dd3d92b90",
  "canteen_id": "8cfb8c75-4e2e-46ee-848b-bec5e4ef7d3b",
  "status": "placed",
  "address": "Room 101, Hostel A",
  "items": [
    {"menu_item_id": "1a4d3c25-7d1d-4da4-ba6e-2c5d070a93d7", "item_name": "Paneer Roll", "quantity": 2, "unit_price": 90.0}
  ],
  "total_price": 308.5
}
```
XML example:
```http
Accept: application/xml
```
```xml
<response>
  <id>e7a0a0fe-1e0d-4f43-9b3d-2b2b356d8fd7</id>
  <customer_id>0d37cfab-4f9c-4eb8-b2d4-bd0dd3d92b90</customer_id>
  <canteen_id>8cfb8c75-4e2e-46ee-848b-bec5e4ef7d3b</canteen_id>
  <status>placed</status>
  <address>Room 101, Hostel A</address>
  <total_price>308.5</total_price>
</response>
```
