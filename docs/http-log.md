# HTTP Request/Response Diagnostics Log

This document records HTTP diagnostic requests executing operations against the JSONPlaceholder public REST API. Each log captures request headers, response headers, body payloads, and critical header annotations.

* **Author:** [Radhika Verma](https://github.com/Radhika-Verma08)
* **Base URL:** `https://jsonplaceholder.typicode.com`
* **Protocol:** `HTTP/1.1` / `HTTPS`

---

## 🔍 Request 1: GET /users/1 (Retrieve User Profile)

### 💻 Command
```bash
curl -i https://jsonplaceholder.typicode.com/users/1
```

### 📤 HTTP Request Headers
```http
GET /users/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
User-Agent: curl/8.4.0
Accept: */*
```

### 📥 HTTP Response Headers
```http
HTTP/1.1 200 OK
Date: Wed, 12 Aug 2026 15:42:10 GMT
Content-Type: application/json; charset=utf-8
Transfer-Encoding: chunked
Connection: keep-alive
X-Powered-By: Express
X-Ratelimit-Limit: 1000
X-Ratelimit-Remaining: 999
X-Ratelimit-Reset: 1786263835
Vary: Origin, Accept-Encoding
Access-Control-Allow-Credentials: true
Cache-Control: max-age=43200
Pragma: no-cache
Expires: -1
ETag: W/"1fd-+2Y3G3w049iSZtw5t1mzSnunngE"
Via: 1.1 vegur
CF-Cache-Status: HIT
Age: 1245
Server: cloudflare
CF-RAY: 7d6c1b3f9b2d8c34-BOM
Alt-Svc: h3=":443"; ma=86400
```

### 📦 Response Body
```json
{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  "address": {
    "street": "Kulas Light",
    "suite": "Apt. 556",
    "city": "Gwenborough",
    "zipcode": "92998-3874",
    "geo": {
      "lat": "-37.3159",
      "lng": "81.1496"
    }
  },
  "phone": "1-770-736-8031 x56442",
  "website": "hildegard.org",
  "company": {
    "name": "Romaguera-Crona",
    "catchPhrase": "Multi-layered client-server neural-net",
    "bs": "harness real-time e-markets"
  }
}
```

### 📝 Header Annotations

| Header Name | Value / Format | Purpose and Meaning |
| :--- | :--- | :--- |
| **Status Code** | `200 OK` | Indicates that the request succeeded and the payload contains the requested user details. |
| **Content-Type** | `application/json; charset=utf-8` | Tells the client that the body content is formatted as JSON, encoded using the UTF-8 character set. |
| **Cache-Control** | `max-age=43200` | Advises intermediaries/browsers that the resource is cacheable for up to 43,200 seconds (12 hours). |
| **CF-Cache-Status**| `HIT` | Indicates that the request was served directly from Cloudflare's edge cache memory rather than forwarding the query to the origin server. |
| **ETag** | `W/"1fd-+2Y3G3w049iSZtw5t1mzSnunngE"` | A weak validator token used for cache revalidation. If the client sends this in `If-None-Match`, the server can return `304 Not Modified`. |
| **X-Ratelimit-Limit**| `1000` | Defines the maximum number of requests allowed within the rate-limit window (1000 requests per window). |
| **X-Ratelimit-Remaining**| `999` | The number of remaining API requests allowed in the current rate limit window. |

---

## ➕ Request 2: POST /posts (Create a New Post)

### 💻 Command
```bash
curl -i -X POST -H "Content-Type: application/json" \
  -d '{"title": "CampusEats Launched", "body": "Order food from your dorm easily!", "userId": 1}' \
  https://jsonplaceholder.typicode.com/posts
```

### 📤 HTTP Request Headers
```http
POST /posts HTTP/1.1
Host: jsonplaceholder.typicode.com
User-Agent: curl/8.4.0
Accept: */*
Content-Type: application/json
Content-Length: 90
```

### 📥 HTTP Response Headers
```http
HTTP/1.1 201 Created
Date: Wed, 12 Aug 2026 15:43:00 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 120
Connection: keep-alive
X-Powered-By: Express
X-Ratelimit-Limit: 1000
X-Ratelimit-Remaining: 998
X-Ratelimit-Reset: 1786263835
Vary: Origin, X-HTTP-Method-Override, Accept-Encoding
Access-Control-Allow-Credentials: true
Cache-Control: no-cache
Pragma: no-cache
Expires: -1
Location: https://jsonplaceholder.typicode.com/posts/101
ETag: W/"78-Zz/wD+lQc1fQW3zIe5O/x21k3k0"
Server: cloudflare
```

### 📦 Response Body
```json
{
  "title": "CampusEats Launched",
  "body": "Order food from your dorm easily!",
  "userId": 1,
  "id": 101
}
```

### 📝 Header Annotations

| Header Name | Value / Format | Purpose and Meaning |
| :--- | :--- | :--- |
| **Status Code** | `201 Created` | Indicates that the request succeeded and resulted in the creation of a new database/server resource. |
| **Location** | `https://jsonplaceholder.typicode.com/posts/101` | Tells the client the absolute URI of the newly created resource, letting them query it directly. |
| **Content-Length** | `120` | Denotes the size of the response payload body in bytes. |
| **Cache-Control** | `no-cache` | Instructs the client not to use a cached copy of this response without first validating it with the origin server (critical for state-changing commands). |

---

## 🔄 Request 3: PUT /users/1 (Update Existing User Profile)

### 💻 Command
```bash
curl -i -X PUT -H "Content-Type: application/json" \
  -d '{"name": "Leanne Graham (Updated)", "email": "leanne.updated@example.com"}' \
  https://jsonplaceholder.typicode.com/users/1
```

### 📤 HTTP Request Headers
```http
PUT /users/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
User-Agent: curl/8.4.0
Accept: */*
Content-Type: application/json
Content-Length: 72
```

### 📥 HTTP Response Headers
```http
HTTP/1.1 200 OK
Date: Wed, 12 Aug 2026 15:44:15 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 81
Connection: keep-alive
X-Powered-By: Express
X-Ratelimit-Limit: 1000
X-Ratelimit-Remaining: 997
X-Ratelimit-Reset: 1786263835
Vary: Origin, Accept-Encoding
Access-Control-Allow-Credentials: true
Cache-Control: no-cache
Pragma: no-cache
Expires: -1
ETag: W/"51-lWdIUpWj+Z6v3wLzOaP4qgYxYvM"
Server: cloudflare
```

### 📦 Response Body
```json
{
  "name": "Leanne Graham (Updated)",
  "email": "leanne.updated@example.com",
  "id": 1
}
```

### 📝 Header Annotations

| Header Name | Value / Format | Purpose and Meaning |
| :--- | :--- | :--- |
| **Status Code** | `200 OK` | The update was successful. The body returns the representation of the updated resource. |
| **HTTP Verb (PUT)**| Idempotent | Re-sending the exact same PUT payload repeatedly produces the identical server state. (Contrast with POST, which creates duplicates). |

---

## 🚫 Request 4: GET /users/999 (Resource Not Found Handling)

### 💻 Command
```bash
curl -i https://jsonplaceholder.typicode.com/users/999
```

### 📤 HTTP Request Headers
```http
GET /users/999 HTTP/1.1
Host: jsonplaceholder.typicode.com
User-Agent: curl/8.4.0
Accept: */*
```

### 📥 HTTP Response Headers
```http
HTTP/1.1 404 Not Found
Date: Wed, 12 Aug 2026 15:45:00 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 2
Connection: keep-alive
X-Powered-By: Express
X-Ratelimit-Limit: 1000
X-Ratelimit-Remaining: 996
X-Ratelimit-Reset: 1786263835
Vary: Origin, Accept-Encoding
Access-Control-Allow-Credentials: true
Cache-Control: max-age=14400
ETag: W/"2-vyYhxUHS2u9Y8Chc8gQzQy3SL4A"
Server: cloudflare
```

### 📦 Response Body
```json
{}
```

### 📝 Header Annotations

| Header Name | Value / Format | Purpose and Meaning |
| :--- | :--- | :--- |
| **Status Code** | `404 Not Found` | The requested URI could not be mapped to any resource on the server. |
| **Content-Length** | `2` | Denotes that the response contains only an empty JSON object `{}`. |
