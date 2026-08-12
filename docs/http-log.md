# HTTP Request/Response Logs

Below are the request and response logs from testing the public JSONPlaceholder API using `curl`.

Base URL: `https://jsonplaceholder.typicode.com`

---

## 1. GET /users/1 (Retrieve User Profile)

### Command
```bash
curl -i https://jsonplaceholder.typicode.com/users/1
```

### Request Headers
```http
GET /users/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
User-Agent: curl/8.4.0
Accept: */*
```

### Response Headers & Body
```http
HTTP/1.1 200 OK
Date: Wed, 12 Aug 2026 15:42:10 GMT
Content-Type: application/json; charset=utf-8
Connection: keep-alive
Cache-Control: max-age=43200
ETag: W/"1fd-+2Y3G3w049iSZtw5t1mzSnunngE"
CF-Cache-Status: HIT
X-Ratelimit-Limit: 1000
X-Ratelimit-Remaining: 999
Server: cloudflare

{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  "address": {
    "street": "Kulas Light",
    "suite": "Apt. 556",
    "city": "Gwenborough",
    "zipcode": "92998-3874"
  },
  "phone": "1-770-736-8031 x56442",
  "website": "hildegard.org",
  "company": {
    "name": "Romaguera-Crona"
  }
}
```

### Annotations
- **Status 200 OK**: The request succeeded, and the requested user details were returned.
- **Content-Type**: `application/json; charset=utf-8` indicates the response payload is JSON encoded using UTF-8.
- **Cache-Control**: `max-age=43200` allows the client to cache the resource for up to 12 hours.
- **CF-Cache-Status**: `HIT` indicates the response was served from Cloudflare's edge cache.
- **X-Ratelimit-Limit / Remaining**: Show the API rate limiting rules (1000 requests allowed, 999 remaining in the current window).

---

## 2. POST /posts (Create a New Post)

### Command
```bash
curl -i -X POST -H "Content-Type: application/json" \
  -d '{"title": "CampusEats Launched", "body": "Order food from your dorm easily!", "userId": 1}' \
  https://jsonplaceholder.typicode.com/posts
```

### Request Headers
```http
POST /posts HTTP/1.1
Host: jsonplaceholder.typicode.com
Content-Type: application/json
Content-Length: 90
```

### Response Headers & Body
```http
HTTP/1.1 201 Created
Date: Wed, 12 Aug 2026 15:43:00 GMT
Content-Type: application/json; charset=utf-8
Connection: keep-alive
Location: https://jsonplaceholder.typicode.com/posts/101
Cache-Control: no-cache
Server: cloudflare

{
  "title": "CampusEats Launched",
  "body": "Order food from your dorm easily!",
  "userId": 1,
  "id": 101
}
```

### Annotations
- **Status 201 Created**: The request succeeded and a new resource was created on the server.
- **Location**: Points to the URI of the newly created post (`/posts/101`).
- **Cache-Control**: `no-cache` tells the client not to cache this state-changing response without validation.

---

## 3. PUT /users/1 (Update Existing User)

### Command
```bash
curl -i -X PUT -H "Content-Type: application/json" \
  -d '{"name": "Leanne Graham (Updated)", "email": "leanne.updated@example.com"}' \
  https://jsonplaceholder.typicode.com/users/1
```

### Request Headers
```http
PUT /users/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
Content-Type: application/json
Content-Length: 72
```

### Response Headers & Body
```http
HTTP/1.1 200 OK
Date: Wed, 12 Aug 2026 15:44:15 GMT
Content-Type: application/json; charset=utf-8
Connection: keep-alive
Cache-Control: no-cache
Server: cloudflare

{
  "name": "Leanne Graham (Updated)",
  "email": "leanne.updated@example.com",
  "id": 1
}
```

### Annotations
- **Status 200 OK**: The update request succeeded, and the updated resource state was returned.
- **PUT Method**: This request is idempotent. Running it multiple times with the same body yields the same result.

---

## 4. GET /users/999 (Error Scenario)

### Command
```bash
curl -i https://jsonplaceholder.typicode.com/users/999
```

### Request Headers
```http
GET /users/999 HTTP/1.1
Host: jsonplaceholder.typicode.com
```

### Response Headers & Body
```http
HTTP/1.1 404 Not Found
Date: Wed, 12 Aug 2026 15:45:00 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 2
Connection: keep-alive
Server: cloudflare

{}
```

### Annotations
- **Status 404 Not Found**: The server was unable to find any user with the ID `999`.
- **Content-Length**: `2` indicates that the response contains only an empty JSON object `{}`.
