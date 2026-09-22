# CS 543 Web Services · Assignment 5
## HTTP Methods & Headers

### 👥 Team & Members (Team No. 11)
* **Nandini Kanaujiya** - `20251651061`
* **Radhika Verma** - `20251651075`
* **Alka Jha** - `20251651013`
* **Alok Mishra** - `20251651014`

---

## Part A · Methods & the Message

### A1. CampusEats Method Map
In accordance with REST design principles, methods directly reflect the action being performed, and no verbs leak into URLs.

| Business Action | HTTP Method | URL Path | Resource Semantics |
|---|---|---|---|
| **Place Order** | `POST` | `/orders` | Creates a new order entity, authorizes payment, registers initial status (`placed`). |
| **Fetch Order** | `GET` | `/orders/{id}` | Retrieves the complete representation of a single order by UUID. |
| **Search / Filter Orders** | `GET` | `/orders` | Queries orders by `customer_id` and/or `status` with sorting and pagination. |
| **Replace / Update Order** | `PUT` | `/orders/{id}` | Replaces editable order fields (`custom_notes`, line items). Protected by `If-Match`. |
| **Purge / Delete Order** | `DELETE` | `/orders/{id}` | Removes a placed or cancelled order from storage. Returns `204 No Content`. |
| **Cancel Order (Non-CRUD)** | `POST` | `/orders/{id}/cancel` | Sub-resource state transition. Cancels order and records audit reason. |
| **Discover Collection Verbs** | `OPTIONS` | `/orders` | Preflight / verb discovery returning `Allow: GET, POST, OPTIONS, HEAD`. |
| **Discover Item Verbs** | `OPTIONS` | `/orders/{id}` | Preflight / verb discovery returning `Allow: GET, PUT, DELETE, OPTIONS, HEAD`. |
| **Legacy Route Redirection** | `GET` | `/order/{id}` | Singular noun redirecting to canonical plural resource via `301 Moved Permanently`. |

---

### A2. Non-CRUD Action Modeling
Actions that represent state-machine transitions or business lifecycle events rather than standard resource replacements cannot be cleanly expressed as PUT/PATCH on an attribute. In CampusEats, order cancellation is modeled as a **POST to a dedicated sub-resource**:
* **Correct REST modeling:** `POST /orders/{id}/cancel` (or `POST /orders/{id}/cancellation`)
* **Violations avoided:** Verbs never appear in top-level URLs (`POST /cancelOrder` is rejected as RPC-style tunneling).
* **State conflicts:** If an order has already transitioned to `cancelled`, `out_for_delivery`, or `delivered`, the sub-resource rejects the operation with `409 Conflict`.

---

### A3. Safe & Idempotent Analysis

| Endpoint | HTTP Method | Safe? | Idempotent? | Naturally Retry-Safe? | Rationale |
|---|---|---|---|---|---|
| `/orders/{id}` | `GET` | **Yes** | **Yes** | **Yes** | Pure read; changes zero server state. Any network retry is completely harmless. |
| `/orders` | `GET` | **Yes** | **Yes** | **Yes** | Pure query/search; zero side effects. Retry-safe across arbitrary proxies. |
| `/orders/{id}` | `OPTIONS` | **Yes** | **Yes** | **Yes** | Discovers metadata and `Allow` capabilities; mutates no state. |
| `/orders/{id}` | `PUT` | **No** | **Yes** | **Yes** | Mutates server state, but repeating identical state replacement yields identical end state. |
| `/orders/{id}` | `DELETE` | **No** | **Yes** | **Yes** | Mutates server state, but once deleted, repeating delete leaves resource deleted (or returns 404). |
| `/orders/{id}/cancel`| `POST` | **No** | **No** | **No** | State-changing lifecycle action. Repeating returns `409 Conflict`. |
| `/orders` | `POST` | **No** | **No** | **No** | Neither safe nor idempotent. Repeated execution creates duplicate orders and double-charges credit cards. **Made retry-safe via `Idempotency-Key`.** |

> **State Invariant:** No `GET` endpoint in this service ever modifies application state, updates counters, or triggers payments.

---

### A4. Reads Take Query Parameters
The order catalogue endpoint (`GET /orders`) stays a pure read and accepts all filtering, sorting, and pagination options via the query string:
* `customer_id` (`UUID`): Filters orders belonging to a specific student.
* `status` (`string`): Filters by state (`placed`, `preparing`, `ready_for_pickup`, `out_for_delivery`, `delivered`, `cancelled`).
* `sort` (`string`): Controls ordering (`ordered_at_desc`, `ordered_at_asc`, `total_price_asc`, `total_price_desc`).
* `page` (`integer`, default: 1): 1-indexed pagination offset.
* `limit` (`integer`, default: 10, max: 100): Page size.

---

### A5. OPTIONS, Allow, and Method Override
* **OPTIONS implementation:** Sending `OPTIONS /orders` returns HTTP status `204 No Content` with `Allow: GET, POST, OPTIONS, HEAD`. Sending `OPTIONS /orders/{id}` returns `Allow: GET, PUT, DELETE, OPTIONS, HEAD`.
* **X-HTTP-Method-Override fallback:** For constrained clients (e.g. legacy corporate proxies, certain form-based clients, or embedded hardware) that cannot emit native `PUT` or `DELETE` packets, the service intercepts `POST` requests bearing the `X-HTTP-Method-Override: PUT` or `X-HTTP-Method-Override: DELETE` header at the WSGI layer, routing them transparently to the update or deletion handlers.

---

### A6. One Full Labeled HTTP Exchange

#### Request
```http
POST /orders HTTP/1.1
Host: api.campuseats.internal
User-Agent: curl/8.21.0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.s6Kj...
Content-Type: application/json
Accept: application/json
Idempotency-Key: 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
Content-Length: 324

{
  "customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3",
  "canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb",
  "items": [
    {
      "menu_item_id": "1e84ceb4-e952-47f6-b0f1-136805a9f5a6",
      "item_name": "Chole Bhature Special",
      "quantity": 2,
      "unit_price": 120.00
    }
  ],
  "delivery_fee": 30.00,
  "custom_notes": "Deliver to Canteen Benches"
}
```

* **Request Line:** `POST /orders HTTP/1.1` (Specifies HTTP verb `POST`, target resource path `/orders`, and protocol version `HTTP/1.1`).
* **Host Header:** `Host: api.campuseats.internal` (Mandatory in HTTP/1.1 for virtual hosting).
* **Authorization Header:** `Authorization: Bearer ...` (Bearer credential identifying the caller).
* **Content-Type Header:** `Content-Type: application/json` (Declares serialization format of request body).
* **Accept Header:** `Accept: application/json` (Content negotiation: declares accepted response format).
* **Idempotency-Key Header:** `Idempotency-Key: 9b1deb4d...` (UUID token guaranteeing safe retries).
* **Content-Length Header:** `Content-Length: 324` (Length of JSON body in octets).
* **Request Body:** JSON payload with validated order parameters.

---

#### Response
```http
HTTP/1.1 201 Created
Date: Sun, 20 Sep 2026 14:41:34 GMT
Server: CampusEats-OrdersService/2.0
Content-Type: application/json
Content-Length: 512
Location: /orders/a989fd1a-dce6-4dcc-9dbd-6f3abd5e8a71
ETag: "8f5a2bd91b1a4329f62299a9b736bdf4"
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 57
X-RateLimit-Reset: 1790001000
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, HEAD

{
  "id": "a989fd1a-dce6-4dcc-9dbd-6f3abd5e8a71",
  "customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3",
  "canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb",
  "status": "placed",
  "items": [
    {
      "menu_item_id": "1e84ceb4-e952-47f6-b0f1-136805a9f5a6",
      "item_name": "Chole Bhature Special",
      "quantity": 2,
      "unit_price": 120.00
    }
  ],
  "subtotal": 240.00,
  "service_fee": 15.00,
  "delivery_fee": 30.00,
  "tax": 12.00,
  "total_price": 297.00,
  "ordered_at": "2026-09-20T14:41:34.128456+00:00",
  "updated_at": "2026-09-20T14:41:34.128456+00:00",
  "cancelled_at": null,
  "cancellation_reason": null,
  "custom_notes": "Deliver to Canteen Benches",
  "version": 1
}
```

* **Status Line:** `HTTP/1.1 201 Created` (Protocol version `HTTP/1.1`, status code `201`, reason phrase `Created`).
* **Location Header:** `Location: /orders/a989fd1a-...` (Canonical URI of the newly created entity).
* **ETag Header:** `ETag: "8f5a2bd91b1a..."` (Strong entity tag representing resource state version).
* **Rate-Limit Headers:** `X-RateLimit-Limit: 60`, `X-RateLimit-Remaining: 57` (Per-client rate budget).
* **Security Headers:** `X-Content-Type-Options: nosniff`, `Strict-Transport-Security: ...` (Prevents MIME sniffing; enforces HTTPS).
* **CORS Headers:** `Access-Control-Allow-Origin: *` (Enables cross-origin browser requests).
* **Response Body:** Published representation of the created order record.

---

## Part D · Headers Matrix (D2)

| Endpoint | Method | Required / Optional Request Headers | Response Headers Set | Status Codes |
|---|---|---|---|---|
| `/orders` | `POST` | **Required:** `Authorization: Bearer <token>`, `Content-Type: application/json`<br/>**Optional:** `Idempotency-Key`, `Accept`, `Accept-Encoding` | `Location`, `ETag`, `Content-Type: application/json`, `X-RateLimit-*`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Access-Control-*`, `Server`, `Date` | `201 Created`<br/>`400 Bad Request`<br/>`401 Unauthorized`<br/>`406 Not Acceptable`<br/>`422 Unprocessable`<br/>`429 Too Many Requests`<br/>`502 Bad Gateway` |
| `/orders/{id}` | `GET` | **Optional:** `If-None-Match`, `Accept`, `Accept-Encoding` | `ETag`, `Cache-Control: private, max-age=60, must-revalidate`, `Content-Type`, `X-RateLimit-*`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Access-Control-*` | `200 OK`<br/>`304 Not Modified`<br/>`400 Bad Request`<br/>`404 Not Found`<br/>`406 Not Acceptable`<br/>`429 Too Many Requests` |
| `/orders` | `GET` | **Optional:** `Accept`, `Accept-Encoding` | `Cache-Control: no-store`, `Content-Type: application/json`, `X-RateLimit-*`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Access-Control-*` | `200 OK`<br/>`400 Bad Request`<br/>`406 Not Acceptable`<br/>`429 Too Many Requests` |
| `/orders/{id}` | `PUT` | **Required:** `Authorization: Bearer <token>`, `If-Match: "<etag>"`, `Content-Type: application/json`<br/>**Optional:** `X-HTTP-Method-Override`, `Accept` | `ETag`, `Content-Type: application/json`, `X-RateLimit-*`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Access-Control-*` | `200 OK`<br/>`400 Bad Request`<br/>`401 Unauthorized`<br/>`404 Not Found`<br/>`409 Conflict`<br/>`412 Precondition Failed`<br/>`422 Unprocessable`<br/>`429 Too Many Requests` |
| `/orders/{id}` | `DELETE` | **Required:** `Authorization: Bearer <token>`<br/>**Optional:** `X-HTTP-Method-Override` | `X-RateLimit-*`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Access-Control-*`, `Server`, `Date` (Empty body) | `204 No Content`<br/>`400 Bad Request`<br/>`401 Unauthorized`<br/>`404 Not Found`<br/>`409 Conflict`<br/>`429 Too Many Requests` |
| `/orders/{id}/cancel` | `POST` | **Required:** `Authorization: Bearer <token>`, `Content-Type: application/json` | `ETag`, `Content-Type: application/json`, `X-RateLimit-*`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Access-Control-*` | `200 OK`<br/>`400 Bad Request`<br/>`401 Unauthorized`<br/>`404 Not Found`<br/>`409 Conflict`<br/>`429 Too Many Requests` |
| `/orders` | `OPTIONS` | None | `Allow: GET, POST, OPTIONS, HEAD`, `Access-Control-*` | `204 No Content` |
| `/orders/{id}` | `OPTIONS` | None | `Allow: GET, PUT, DELETE, OPTIONS, HEAD`, `Access-Control-*` | `204 No Content` |
| `/order/{id}` | `GET` | None | `Location: /orders/{id}`, `Strict-Transport-Security`, `Server`, `Date` | `301 Moved Permanently` |

---

## Part C · Safe-Retry Plan (C4)

| Risky Operation | Safe? | Idempotent? | Failure / Risk Scenario | Mechanism Applied | Engineering Rationale |
|---|---|---|---|---|---|
| **Place Order (`POST /orders`)** | No | No | Network timeout after payment charge causes client to re-submit order. Without protection, student is double-billed and canteen cooks duplicate food. | **`Idempotency-Key`** | Ensures server recognizes repeat attempts with the same key, returning the original `201 Created` payload from cache without re-charging or creating duplicate records. |
| **Read Order (`GET /orders/{id}`)** | Yes | Yes | High-frequency client polling (mobile app checking order preparation status) burns server CPU and bandwidth transferring unchanged JSON. | **`If-None-Match` &rarr; `304 Not Modified`** | Server validates client's cached ETag against current order state. If identical, returns empty body with `304 Not Modified`, cutting 98% of network bandwidth. |
| **Update Order (`PUT /orders/{id}`)** | No | Yes | Two canteens or user and admin simultaneously update notes/status. The second write silently clobbers the first ("Lost Update" problem). | **`If-Match` &rarr; `412 Precondition Failed`** | Forces client to supply the ETag it based its edit on. If the order was modified in the interim, the write is aborted with 412, preventing race conditions. |
| **Cancel Order (`POST /orders/{id}/cancel`)** | No | No | Repeated cancel requests on an order that has already transitioned to cancelled or delivered. | **State Machine Check &rarr; `409 Conflict`** | Validates internal lifecycle invariants. Once cancelled, repeated requests receive 409 Conflict rather than creating corrupted refund records. |

---

## Answers to Mandatory Questions (D3)

### Question 1
**For three of your endpoints, give the method, the success status, and the single response header that matters most — and why.**

1. **`POST /orders`**
   * **Success Status:** `201 Created`
   * **Most Critical Response Header:** `Location: /orders/{id}`
   * **Why:** In REST, resource creation decouples the client from database ID generation. Returning `201 Created` without a `Location` header leaves the client stranded without knowledge of where the newly minted entity lives. The `Location` header provides the absolute/canonical URI to identify, fetch, and bookmark the created order.
2. **`GET /orders/{id}`**
   * **Success Status:** `200 OK` (or `304 Not Modified`)
   * **Most Critical Response Header:** `ETag: "{hash}"`
   * **Why:** The ETag acts as an authoritative fingerprint of the resource's current state. It powers client-side caching (via `If-None-Match`), eliminating redundant data transfers on reads, and simultaneously powers optimistic concurrency control (via `If-Match`), protecting updates from being clobbered.
3. **`DELETE /orders/{id}`**
   * **Success Status:** `204 No Content`
   * **Most Critical Response Header:** `X-Content-Type-Options: nosniff` (or `Allow` on `OPTIONS`)
   * **Why:** A `204 No Content` response has no body, making content headers irrelevant. However, security headers like `X-Content-Type-Options: nosniff` ensure intermediate agents and browsers do not attempt to guess or synthesize content types on state-destroying requests, preventing malicious MIME-confusion attacks.

---

### Question 2
**Which of your endpoints are safe, and which are idempotent? Which one is neither, and how did you make it retry-safe?**

* **Safe Endpoints:** `GET /orders/{id}`, `GET /orders`, `OPTIONS /orders`, `OPTIONS /orders/{id}`, `GET /order/{id}` (redirect).
  * *Why:* According to RFC 7231 Section 4.2.1, safe methods are read-only. Calling them 1,000 times will not mutate server state or alter business records.
* **Idempotent Endpoints:** All safe endpoints above, plus `PUT /orders/{id}` and `DELETE /orders/{id}`.
  * *Why:* Repeating a `PUT` with the same payload leaves the resource in the exact same state. Repeating a `DELETE` leaves the resource deleted.
* **Neither Safe Nor Idempotent:** `POST /orders`.
  * *Why:* `POST /orders` triggers financial payment charging, creates a new database row with a unique UUID, and sends an alert to the canteen kitchen. If a network blip occurs during transit, resending a raw `POST` would charge the student twice and cook two identical meals.
  * **How we made it retry-safe:** We implemented the **`Idempotency-Key`** header pattern. When the client sends `POST /orders`, it attaches a unique idempotency UUID. The server stores the resulting `201 Created` response payload and `Location` under this key. If the network drops and the client safely re-executes the exact same request with the same `Idempotency-Key`, the server intercepts it before payment execution and returns the original cached response with `X-Cache-Lookup: HIT-IDEMPOTENT`, ensuring zero duplicate payments or orders.

---

### Question 3
**Show one ETag from your service, the request that returns 304, and the write that returns 412. What does each save or prevent?**

* **ETag from CampusEats service:** `"8f5a2bd91b1a4329f62299a9b736bdf4"` (Calculated as MD5 hash over order ID, version counter, total price, status, items, and updated timestamp).
* **Request returning 304 Not Modified:**
  ```http
  GET /orders/a989fd1a-dce6-4dcc-9dbd-6f3abd5e8a71 HTTP/1.1
  Host: api.campuseats.internal
  If-None-Match: "8f5a2bd91b1a4329f62299a9b736bdf4"
  ```
  * **What it saves:** Saves network bandwidth, reduces server JSON serialization CPU cycles, minimizes mobile client battery drain, and avoids unnecessary DOM re-rendering on the client UI.
* **Write returning 412 Precondition Failed:**
  ```http
  PUT /orders/a989fd1a-dce6-4dcc-9dbd-6f3abd5e8a71 HTTP/1.1
  Host: api.campuseats.internal
  Authorization: Bearer test-token
  Content-Type: application/json
  If-Match: "stale-etag-value-12345"

  {
    "custom_notes": "Deliver strictly to Room 304"
  }
  ```
  * **What it prevents:** Prevents the classic **"Lost Update" problem**. If Editor A and Editor B both read the order at Version 1, and Editor A updates it first (advancing it to Version 2), Editor B's request will still carry Editor A's old ETag. The server detects this mismatch and rejects Editor B's write with `412 Precondition Failed`, preventing Editor B from silently overwriting Editor A's changes.

---

### Question 4
**You return 422 for one case and 400 for another. Give the exact request that triggers each, and explain the difference.**

#### Exact Request Triggering 400 Bad Request:
```http
POST /orders HTTP/1.1
Host: api.campuseats.internal
Authorization: Bearer test-token
Content-Type: application/json

{customer_id: "not-quoted-invalid-json"}
```
*or missing mandatory field:*
```json
{
  "customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3"
}
```

#### Exact Request Triggering 422 Unprocessable Entity:
```http
POST /orders HTTP/1.1
Host: api.campuseats.internal
Authorization: Bearer test-token
Content-Type: application/json

{
  "customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3",
  "canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb",
  "items": []
}
```

#### Explanation of Difference:
* **`400 Bad Request` represents Syntactic/Structural Failure:** The server cannot parse the payload, the JSON syntax is broken, or fundamental required envelope attributes are completely missing. The request failed basic input decoding.
* **`422 Unprocessable Entity` represents Semantic/Domain Invariant Violation:** The JSON is 100% syntactically valid and well-formed, all required keys exist, and data types match. However, the business domain refuses the operation because the values violate business rules (e.g. an order cannot have zero line items; a line item cannot have negative quantity; or an external payment token has insufficient funds).

---

### Question 5
**A browser page on another origin calls your API and is blocked — yet your server logs show a 200. Who blocked it, and which response header fixes it?**

* **Who blocked it:** The **Client's Web Browser** blocked it by enforcing the **Same-Origin Policy (SOP)**.
* **Why the server logs show a 200:** The browser actually dispatched the cross-origin HTTP request across the network, the backend server processed it successfully, and the server returned `200 OK`. However, because the server response did not include Cross-Origin Resource Sharing (CORS) permission headers, the browser's security sandbox quarantined the response and refused to expose it to the JavaScript application runtime.
* **Which response header fixes it:**
  ```http
  Access-Control-Allow-Origin: *
  ```
  *(or reflecting the caller's origin: `Access-Control-Allow-Origin: https://student.campuseats.edu`)*
  For preflighted requests (e.g., requests carrying `Authorization` or `Content-Type: application/json`), the server must also answer `OPTIONS` preflight requests with:
  ```http
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, HEAD
  Access-Control-Allow-Headers: Authorization, Content-Type, Accept, If-None-Match, If-Match, Idempotency-Key, X-HTTP-Method-Override
  ```

---

### Question 6
**Name one response where you set Cache-Control to allow caching and one where you must use no-store. Why each?**

1. **Where we set `Cache-Control` to allow caching:**
   * **Endpoint:** `GET /orders/{id}`
   * **Header Value:** `Cache-Control: private, max-age=60, must-revalidate`
   * **Why:** A specific order's details (line items, total price, timestamps) rarely change once placed. Allowing the student's client browser to cache this representation for 60 seconds minimizes load on our database. We mark it `private` so that intermediate corporate/campus forward proxies do not store personal order records and leak them to other students. We include `must-revalidate` so that expired caches cannot serve stale order statuses.
2. **Where we must use `no-store`:**
   * **Endpoint:** `GET /orders` (Order list & search query)
   * **Header Value:** `Cache-Control: no-store`
   * **Why:** A query for orders is dynamic and highly time-sensitive; new orders are continually placed and kitchen statuses transition from `preparing` to `ready`. If a browser or proxy cached the output of `GET /orders?customer_id=...`, the student's active order dashboard would show stale order lists or falsely report that an order has not yet been placed. `no-store` mandates that no client or proxy ever writes the response to disk or cache storage.

---

### Question 7
**Your search endpoint is a GET. When would POST be the right choice instead, and what do you give up by switching?**

* **When `POST` would be the right choice:**
  1. **Excessive Query Complexity & URL Length Overflow:** When a search request requires deep nested query syntax, multiple multi-select filters, complex Boolean logic trees, or large geographical coordinate polygons (e.g., campus delivery bounding box coordinates) that exceed URL length limits (typically ~2,048 characters in Internet Explorer/Edge and HTTP proxies).
  2. **Sensitive Data Protection in Search Criteria:** When the query filter contains sensitive personally identifiable information (PII) or secrets. URLs are logged in plain text in browser history, proxy server access logs, and `Referer` headers. A `POST` encapsulates search criteria in the encrypted TLS message body.
* **What you give up by switching to `POST`:**
  1. **Automatic HTTP Cacheability:** Intermediate CDNs, reverse proxies, and browser caches natively cache `GET` responses based on URL keys; `POST` is non-idempotent by default and will not be cached without complex custom caching directives.
  2. **Bookmarkability and Link Shareability:** Users cannot bookmark a search result or email the URL to a teammate, because the search criteria are not in the URI.
  3. **Safe Automatic Retries:** Browsers and HTTP libraries know that `GET` is safe and idempotent and can automatically retry failed connection drops. For `POST`, browsers pop up warning dialogs: *"Are you sure you want to resubmit this form?"*

---

### Question 8
**Location appears on a 201 and on a 3xx. What does it point to in each case?**

* **On a `201 Created`:**
  * **What it points to:** It points to the **Newly Created Resource's Canonical URI** (e.g., `Location: /orders/a989fd1a-dce6-4dcc-9dbd-6f3abd5e8a71`).
  * **Purpose:** It tells the client: *"Your creation request succeeded; here is the persistent URI where your new entity lives and can be fetched in the future."*
* **On a `3xx Redirection` (e.g., `301 Moved Permanently` or `308 Permanent Redirect`):**
  * **What it points to:** It points to the **Target Destination URI** where the resource has been relocated (e.g. our legacy endpoint `GET /order/{id}` returns `Location: /orders/{id}`).
  * **Purpose:** It instructs the user agent / browser: *"The resource you asked for is not here; follow this Location header immediately to find the requested content at its new address."*
