# CS 543 Web Services · Assignment 4
## Rebuilding a CampusEats Service in REST

### 👥 Team & Members (Team No. 10)
* **Nandini Kanaujiya** - `20251651061`
* **Radhika Verma** - `20251651075`
* **Alka Jha** - `20251651013`
* **Alok Mishra** - `20251651014`

---

## Part A · Model the Service

### A1. Selected Service
We selected the **Orders Service** from the CampusEats system boundary defined in Assignment 2. The Orders Service owns the `orders` and `order_items` tables and logically references the User Service (`customer_id`), Canteen Service (`canteen_id`, `menu_item_id`), and external Payments Service.

### A2. Operations Written in SOAP Style
If designed using Assignment 3 WSDL/SOAP style, the operations would have been:
1. `createOrder(customerId, canteenId, items[], deliveryFee, paymentToken)`
2. `getOrder(orderId)`
3. `listOrdersByCustomer(customerId, status)`
4. `cancelOrder(orderId, reason)`

### A3. Finding the Nouns
In REST, verbs must never appear in URLs. Each operation is mapped to durable nouns:
- `createOrder` &rarr; Plural noun: `/orders`
- `getOrder` &rarr; Single item noun: `/orders/{id}`
- `listOrdersByCustomer` &rarr; Filtered collection noun: `/orders?customer_id=...&status=...`
- `cancelOrder` &rarr; Sub-resource noun representing lifecycle transition: `/orders/{id}/cancellation`

### A4. Resource Table

| HTTP Method | URL | What It Does | Success Code | Failure Codes |
|---|---|---|---|---|
| `POST` | `/orders` | Creates an order record, calculates fees/tax, and charges payment via outbound partner | `201 Created` | `400 Bad Request`<br/>`422 Unprocessable Entity`<br/>`502 Bad Gateway` |
| `GET` | `/orders/{id}` | Retrieves the public representation of a single order by UUID | `200 OK` | `400 Bad Request`<br/>`404 Not Found` |
| `GET` | `/orders` | Retrieves a filtered list of orders by `customer_id` and/or `status` | `200 OK` | `400 Bad Request` |
| `POST` | `/orders/{id}/cancellation` | State-changing sub-resource that transitions order status to `cancelled` | `200 OK` | `400 Bad Request`<br/>`404 Not Found`<br/>`409 Conflict` |

### A5. Justification of One Hard Choice
The operation that mapped least comfortably onto a resource was **Order Cancellation**. In SOAP/RPC, cancellation is treated as a procedure call: `cancelOrder(orderId, reason)`. In REST, URLs containing verbs (e.g., `POST /orders/{id}/cancel`) violate resource orientation. We considered and rejected `DELETE /orders/{id}` because an order is a binding financial transaction and legal record; erasing it from storage would destroy accounting audit trails. We also considered `PATCH /orders/{id}` with `{"status": "cancelled"}` but rejected it because cancellation is not merely modifying an attribute—it evaluates complex business invariants (verifying the order has not been prepared/delivered, issuing refunds, and triggering kitchen notifications). We resolved this by treating cancellation as a first-class sub-resource: `POST /orders/{id}/cancellation`. This clearly models the creation of a cancellation event and returns `409 Conflict` if the current lifecycle state rejects the transition.

---

## Part D · Network Resilience & Fallback

### D3. Fallback Reasoning
When the external Payment Service dependency is unreachable or fails after all exponential backoff retries with jitter, the Orders Service chooses to **fail fast** by returning `502 Bad Gateway` with an RFC 7807 problem detail payload (`type: "https://campuseats.internal/errors/bad-gateway"`), rather than silently degrading. 

In a campus food delivery network, **degrading would be unacceptable and financially dangerous**. If CampusEats degraded by accepting orders in a speculative "pending payment" state, canteen kitchens would immediately incur real labor and ingredient costs cooking meals for orders that may never clear payment. Furthermore, allowing students to place orders on an unverified credit balance would create major chargeback risks and reconciliation deficits. Failing fast protects kitchen resources and immediately informs the student to try again or choose an alternate payment method.

---

## Answers to Mandatory Questions

### Question 1: WSDL vs OpenAPI Line Count & Differences
* **Assignment 3 WSDL (`partner.wsdl`):** 100 lines (defines 1 operation: `processPayment`).
* **Assignment 4 OpenAPI (`openapi.yaml`):** 377 lines (defines 4 operations across 3 resource paths).

**What the difference is made of:**
The line count difference reflects the shift from an isolated RPC operation to a full-lifecycle resource model. The OpenAPI contract documents complete HTTP semantics for multiple operations: path parameters, query filters, headers (`Idempotency-Key`, `Location`), multiple response status codes (`200`, `201`, `400`, `404`, `409`, `422`, `502`), reusable RFC 7807 problem structures, and realistic request/response payload examples.

**Two things the WSDL declared that OpenAPI does not need to:**
1. **Abstract Message Declarations (`<wsdl:message>` and `<wsdl:part>`):** WSDL required decoupling type definitions from operations by introducing an intermediate `<wsdl:message>` abstraction. OpenAPI eliminates this boilerplate by referencing data schemas directly within the operation's `requestBody` and `responses`.
2. **Explicit Transport and Envelope Bindings (`<wsdl:binding>` and `<soap:binding>`):** WSDL had to specify transport protocols (`transport="http://schemas.xmlsoap.org/soap/http"`), style (`document`), and SOAP envelope serialization rules (`<soap:body use="literal"/>`). OpenAPI operates directly on the native HTTP application layer, assuming standard HTTP methods, status codes, and MIME types (`application/json`) without redundant transport binding declarations.

---

### Question 2: SOAP Fault vs REST Status & Problem Body
**Quoted `soap:Fault` from Assignment 3:**
```xml
<soapenv:Fault>
   <faultcode>soapenv:Client</faultcode>
   <faultstring>Card Declined: Insufficient Funds</faultstring>
   <detail>
      <types:paymentFault xmlns:types="http://securepay.com/payment/types/">
         <types:errorCode>SP-402</types:errorCode>
         <types:errorMessage>The transaction was declined by the issuing bank due to insufficient funds in the account.</types:errorMessage>
      </types:paymentFault>
   </detail>
</soapenv:Fault>
```

**Replacement REST HTTP Status & RFC 7807 Problem Body:**
* **HTTP Status:** `422 Unprocessable Entity` (or `400 Bad Request`)
* **Response Body (`application/problem+json`):**
```json
{
  "type": "https://campuseats.internal/errors/payment-declined",
  "title": "Payment Declined",
  "status": 422,
  "detail": "Upstream payment was declined: Payment declined: insufficient account balance.",
  "instance": "/orders/d729bf70-2ac6-4cdb-ab17-65691f8604e8"
}
```

**Why returning that error inside a `200 OK` is a problem for the network in between:**
1. **Cache Pollution at Intermediate Proxies/CDNs:** Reverse proxies and edge caches (Cloudflare, Varnish, NGINX) rely on HTTP response codes to manage caching. If an error is returned with `200 OK`, a proxy may cache the error response and serve it to subsequent legitimate requests, leading to widespread application breakage.
2. **Breakdown of Infrastructure Monitoring & Circuit Breakers:** API gateways and observability tooling (Envoy, Prometheus, Datadog) inspect HTTP status codes to track error rates, compute SLOs, and trigger automated circuit breaking. When failures are disguised under `200 OK`, middleboxes perceive 100% health, masking outages from engineering teams and preventing automatic failovers.

---

### Question 3: UDDI Moves (Publish, Find, Bind)
* **What Disappeared:**
  - **Publish** via UDDI registries (with complex `save_business`, `save_service`, `save_tModel` XML SOAP calls) disappeared completely.
  - **Find** via runtime UDDI queries (`find_business`, `find_service`) is completely obsolete.
* **What Took Over:**
  - **Publish:** Modern API developer portals (SwaggerHub, Backstage, GitHub repositories, and automated CI/CD pipelines) where machine-readable `openapi.yaml` contracts and interactive Swagger UI documentations are published.
  - **Find:** Infrastructure-level service discovery mechanisms, such as Kubernetes DNS, Consul, AWS Cloud Map, API Gateways, and environment variables (e.g., `PAYMENT_SERVICE_URL`).
* **What Still Exists:**
  - **Bind:** The consumer still needs to know the endpoint address, data schemas, and transport rules to format requests. In our modern setup, binding is performed using OpenAPI client code generators (OpenAPI Generator, Swagger Codegen), typed SDKs, or standard HTTP client libraries (`requests`, `fetch`, `axios`) that directly bind to the documented REST resources.

---

### Question 4: Schema Enforcement & Validation Responsibility
* **Enforcing Function in Code:** `validate_order_payload(data)` (and `validate_cancellation_payload(data)`) located in `models.py`, executed explicitly at the entry point of route handlers in `app.py` before any business logic touches the fields.
* **Failure That Would Get Through If Not Written:**
  If this manual validation function were omitted, a request with an empty items list (`"items": []"`) or negative item quantities (`"quantity": -5"`) would pass into the `Order` constructor. Calculating total price on negative quantities would produce an invalid order total, corrupting accounting balances and charging students negative amounts. Without validation, requests missing mandatory keys (`customer_id`, `canteen_id`) would trigger unhandled Python `KeyError` exceptions, crashing with unformatted `500 Internal Server Error` responses rather than clean, informative `400 Bad Request` or `422 Unprocessable Entity` problem details.

---

### Question 5: Where SOAP Would Still Be Chosen Over REST
* **Chosen Service Edge:** The inter-bank settlement and high-value reconciliation clearing channel between the CampusEats payment adapter and the bank core banking network.
* **Guarantees Bought:**
  1. **WS-AtomicTransaction (ACID / Two-Phase Commit):** Provides native, protocol-level distributed transaction coordination across heterogeneous banking databases. This guarantees that charging the customer account, crediting the merchant escrow, and logging the clearing ledger either commit simultaneously or abort cleanly, preventing partial failures.
  2. **WS-Security (End-to-End Message-Level Security & Non-Repudiation):** Unlike REST (which relies on transport-layer TLS terminated at each reverse proxy or load balancer), WS-Security provides XML Digital Signatures (`ds:Signature`) and XML Encryption (`xenc:EncryptedData`) directly on message fragments. This ensures that sensitive banking data remains encrypted and cryptographically signed across multi-hop transit networks, providing legally binding non-repudiation that protects against financial fraud and disputes.

---

## Verification & Execution Outputs

### 1. OpenAPI Validator Output (Zero Errors)
```text
c:\AI Coding Challenge Platform\Assignment-4\openapi.yaml: OK
```
*Validation command executed:* `python -m openapi_spec_validator Assignment-4/openapi.yaml` (Exit Code 0).

---

### 2. Pytest Test Suite Output (4 Passing Tests)
```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\AI Coding Challenge Platform
plugins: anyio-4.13.0
collected 4 items

Assignment-4/tests/test_orders.py::test_create_order_success PASSED      [ 25%]
Assignment-4/tests/test_orders.py::test_create_order_idempotent_repeat PASSED [ 50%]
Assignment-4/tests/test_orders.py::test_failure_paths_return_right_4xx PASSED [ 75%]
Assignment-4/tests/test_orders.py::test_unknown_id_returns_404 PASSED    [100%]

============================== 4 passed in 0.43s ==============================
```

---

### 3. Live Curl Transcript (`curl -i`)
Captured from the running Orders service demonstrating all required paths:

#### Scenario 1: Successful Order Creation (`201 Created` with `Location` header)
```http
POST /orders HTTP/1.1
Host: localhost:5000
Content-Type: application/json
Idempotency-Key: idemp-student-demo-10

{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "items": [
    {
      "menu_item_id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
      "item_name": "Veg Thali Deluxe",
      "quantity": 2,
      "unit_price": 120.00
    }
  ],
  "delivery_fee": 30.00,
  "payment_token": "tok_visa_4242",
  "custom_notes": "Leave at Hostel 4 entrance"
}

HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/json
Content-Length: 626
Location: /orders/d729bf70-2ac6-4cdb-ab17-65691f8604e8
Connection: close

{
  "cancellation_reason": null,
  "cancelled_at": null,
  "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "custom_notes": "Leave at Hostel 4 entrance",
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "delivery_fee": 30.0,
  "id": "d729bf70-2ac6-4cdb-ab17-65691f8604e8",
  "items": [
    {
      "item_name": "Veg Thali Deluxe",
      "menu_item_id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
      "quantity": 2,
      "unit_price": 120.0
    }
  ],
  "ordered_at": "2026-09-02T19:46:58.772473+00:00",
  "service_fee": 15.0,
  "status": "placed",
  "subtotal": 240.0,
  "tax": 12.0,
  "total_price": 297.0
}
```

#### Scenario 2: Safe Idempotent Repeat (Duplicate `Idempotency-Key` returns original)
```http
POST /orders HTTP/1.1
Host: localhost:5000
Content-Type: application/json
Idempotency-Key: idemp-student-demo-10

HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/json
Content-Length: 626
Location: /orders/d729bf70-2ac6-4cdb-ab17-65691f8604e8
X-Cache-Lookup: HIT-IDEMPOTENT
Connection: close

{
  "cancellation_reason": null,
  "cancelled_at": null,
  "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "custom_notes": "Leave at Hostel 4 entrance",
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "delivery_fee": 30.0,
  "id": "d729bf70-2ac6-4cdb-ab17-65691f8604e8",
  "items": [
    {
      "item_name": "Veg Thali Deluxe",
      "menu_item_id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
      "quantity": 2,
      "unit_price": 120.0
    }
  ],
  "ordered_at": "2026-09-02T19:46:58.772473+00:00",
  "service_fee": 15.0,
  "status": "placed",
  "subtotal": 240.0,
  "tax": 12.0,
  "total_price": 297.0
}
```

#### Scenario 3: Single Resource Retrieval (`200 OK`)
```http
GET /orders/d729bf70-2ac6-4cdb-ab17-65691f8604e8 HTTP/1.1
Host: localhost:5000

HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/json
Content-Length: 626
Connection: close

{
  "cancellation_reason": null,
  "cancelled_at": null,
  "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "custom_notes": "Leave at Hostel 4 entrance",
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "delivery_fee": 30.0,
  "id": "d729bf70-2ac6-4cdb-ab17-65691f8604e8",
  "items": [
    {
      "item_name": "Veg Thali Deluxe",
      "menu_item_id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
      "quantity": 2,
      "unit_price": 120.0
    }
  ],
  "ordered_at": "2026-09-02T19:46:58.772473+00:00",
  "service_fee": 15.0,
  "status": "placed",
  "subtotal": 240.0,
  "tax": 12.0,
  "total_price": 297.0
}
```

#### Scenario 4: State-Changing Sub-resource: Order Cancellation (`200 OK`)
```http
POST /orders/d729bf70-2ac6-4cdb-ab17-65691f8604e8/cancellation HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "reason": "Student requested cancellation before food preparation began"
}

HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/json
Content-Length: 717
Connection: close

{
  "cancellation_reason": "Student requested cancellation before food preparation began",
  "cancelled_at": "2026-09-02T19:47:01.911959+00:00",
  "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "custom_notes": "Leave at Hostel 4 entrance",
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "delivery_fee": 30.0,
  "id": "d729bf70-2ac6-4cdb-ab17-65691f8604e8",
  "items": [
    {
      "item_name": "Veg Thali Deluxe",
      "menu_item_id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
      "quantity": 2,
      "unit_price": 120.0
    }
  ],
  "ordered_at": "2026-09-02T19:46:58.772473+00:00",
  "service_fee": 15.0,
  "status": "cancelled",
  "subtotal": 240.0,
  "tax": 12.0,
  "total_price": 297.0
}
```

#### Scenario 5: State Conflict (`409 Conflict` on Repeat Cancellation)
```http
POST /orders/d729bf70-2ac6-4cdb-ab17-65691f8604e8/cancellation HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "reason": "Student requested cancellation before food preparation began"
}

HTTP/1.1 409 CONFLICT
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/problem+json
Content-Length: 286
Connection: close

{
  "detail": "Order 'd729bf70-2ac6-4cdb-ab17-65691f8604e8' has already been cancelled previously.",
  "instance": "/orders/d729bf70-2ac6-4cdb-ab17-65691f8604e8/cancellation",
  "status": 409,
  "title": "State Conflict",
  "type": "https://campuseats.internal/errors/state-conflict"
}
```

#### Scenario 6: Malformed Body (`400 Bad Request`)
```http
POST /orders HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}

HTTP/1.1 400 BAD REQUEST
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/problem+json
Content-Length: 185
Connection: close

{
  "detail": "Missing mandatory field 'customer_id'.",
  "instance": "/orders",
  "status": 400,
  "title": "Bad Request",
  "type": "https://campuseats.internal/errors/bad-request"
}
```

#### Scenario 7: Domain Validation Refusal (`422 Unprocessable Entity`)
```http
POST /orders HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "items": []
}

HTTP/1.1 422 UNPROCESSABLE ENTITY
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/problem+json
Content-Length: 210
Connection: close

{
  "detail": "An order must contain at least one line item.",
  "instance": "/orders",
  "status": 422,
  "title": "Unprocessable Entity",
  "type": "https://campuseats.internal/errors/unprocessable-entity"
}
```

#### Scenario 8: Missing Resource Lookup (`404 Not Found`)
```http
GET /orders/00000000-0000-0000-0000-000000000000 HTTP/1.1
Host: localhost:5000

HTTP/1.1 404 NOT FOUND
Server: Werkzeug/3.1.8 Python/3.13.5
Content-Type: application/problem+json
Content-Length: 264
Connection: close

{
  "detail": "Order with ID '00000000-0000-0000-0000-000000000000' was not found in the catalogue.",
  "instance": "/orders/00000000-0000-0000-0000-000000000000",
  "status": 404,
  "title": "Not Found",
  "type": "https://campuseats.internal/errors/not-found"
}
```
