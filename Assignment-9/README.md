# CS543 Assignment 09: Securing the API

## CampusEats Catalogue API

**Course:** CS543 – Web Services  
**Assignment:** Assignment 09 – Securing the API  
**Institute:** Indian Institute of Information Technology Vadodara (IIIT Vadodara)  
**Academic Session:** 2026–27  
**Team:** 11

---

## 1. Team 11 Members

| S. No. | Member Name | University Registration Number |
|---|---|---|
| 1 | Raddika Verma | 20251651075 |
| 2 | Nandini Kanaujiya | 20251651061 |
| 3 | Alka Jha | 20251651013 |
| 4 | Alok Mishra | 20251651014 |

---

## 2. Introduction

CampusEats Catalogue API is a RESTful web service developed using Node.js and Express.js. It provides operations to manage a food catalogue, including retrieving menu items, adding new items, and deleting existing items.

This project is based on the REST service developed in Assignment 08. Assignment 09 extends the existing service by implementing authentication and role-based authorization to secure the API endpoints.

The API uses JSON Web Tokens (JWT) for authentication and bcrypt for password verification. Different users are assigned different roles, and access to protected operations is controlled according to their permissions.

## 3. Objectives

- Implement user authentication using username and password.
- Securely verify passwords using bcrypt.
- Generate and verify JSON Web Tokens.
- Protect API routes using authentication middleware.
- Implement role-based authorization.
- Restrict menu modification operations to authorized users.
- Test authentication and authorization using Thunder Client.

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Node.js | JavaScript runtime |
| Express.js | REST API development |
| bcryptjs | Password hashing and verification |
| jsonwebtoken | JWT generation and verification |
| dotenv | Environment variable configuration |
| Thunder Client | API testing |
| HTML, CSS, JavaScript | Frontend interface |

## 5. Project Structure

```text
catalogue/
│
├── public/
│   └── index.html
│
├── server.js
├── package.json
├── package-lock.json
├── .env
├── .env.example
├── .gitignore
└── README.md
```

The `node_modules` directory contains installed dependencies and should not be uploaded to GitHub.

## 6. Installation and Setup

### Prerequisites

- Node.js
- npm
- Visual Studio Code
- Thunder Client extension

### Install dependencies

```bash
npm install
```

### Configure environment variables

Create a `.env` file in the project root.

```env
JWT_SECRET=your_secret_key_here
```

Replace the placeholder with a strong, private secret.

### Start the server

```bash
node server.js
```

The server starts at:

```text
http://localhost:3000
```

The frontend can be accessed through the same address.

## 7. User Roles

The application uses two user roles.

| Role | Username | Password | Permissions |
|---|---|---|---|
| Customer | alice | alice123 | View catalogue and individual items |
| Restaurant | restaurant1 | rest123 | View catalogue, add items, and delete items |

Passwords are hashed using bcrypt before being stored in the application's user data.

## 8. Authentication

Authentication is implemented using JSON Web Tokens.

### Login Endpoint

**Method:** POST  
**Endpoint:** `/login`  
**Authentication:** Not required

Request:

```json
{
  "username": "restaurant1",
  "password": "rest123"
}
```

Successful response:

```json
{
  "message": "login successful",
  "token": "<JWT_TOKEN>"
}
```

The token contains the user's ID and role and is configured to expire after one hour.

### Authentication Process

1. The user submits their username and password.
2. The application searches for the corresponding user.
3. The submitted password is verified using bcrypt.
4. If the credentials are valid, the server generates a JWT.
5. The token is returned to the client.
6. The client includes the token in subsequent protected requests.

If the username or password is incorrect, the API returns:

**Status:** `401 Unauthorized`

```json
{
  "error": "invalid username or password"
}
```

## 9. JWT Authentication Middleware

The authentication middleware protects API routes.

It reads the JWT from the request's Authorization header.

Required header:

```text
Authorization: Bearer <JWT_TOKEN>
```

The middleware verifies the token using the JWT secret.

- Missing token: `401 Unauthorized`
- Invalid token: `401 Unauthorized`
- Expired token: `401 Unauthorized`
- Valid token: Request proceeds to the next middleware or route handler.

The authenticated user's information is attached to the request for subsequent authorization checks.

## 10. Role-Based Authorization

The application implements role-based authorization using middleware.

The `requireRole()` middleware checks whether the authenticated user has permission to perform the requested operation.

| Operation | Customer | Restaurant |
|---|---|---|
| Login | Allowed | Allowed |
| GET `/items` | Allowed | Allowed |
| GET `/items/:id` | Allowed | Allowed |
| POST `/items` | Forbidden | Allowed |
| DELETE `/items/:id` | Forbidden | Allowed |

Customers can access catalogue information but cannot modify menu items.

Restaurant users can perform both read and write operations.

If an authenticated user does not have the required role, the API returns:

**Status:** `403 Forbidden`

```json
{
  "error": "forbidden: insufficient permissions"
}
```

## 11. API Endpoints

Base URL:

```text
http://localhost:3000
```

### 11.1 Login

**Method:** POST  
**Endpoint:** `/login`  
**Authentication:** Not required

Request:

```json
{
  "username": "restaurant1",
  "password": "rest123"
}
```

Returns a JWT token on successful authentication.

### 11.2 Get All Catalogue Items

**Method:** GET  
**Endpoint:** `/items`  
**Authentication:** Required  
**Allowed roles:** Customer, Restaurant

Returns all catalogue items.

An optional vegetarian filter is supported:

```text
GET /items?veg=true
```

### 11.3 Get Catalogue Item by ID

**Method:** GET  
**Endpoint:** `/items/:id`  
**Authentication:** Required  
**Allowed roles:** Customer, Restaurant

Example:

```text
GET /items/1
```

If the item does not exist:

```json
{
  "error": "not found"
}
```

Status: `404 Not Found`

### 11.4 Add Catalogue Item

**Method:** POST  
**Endpoint:** `/items`  
**Authentication:** Required  
**Allowed role:** Restaurant

Request:

```json
{
  "name": "Masala Dosa",
  "price": 120,
  "veg": true
}
```

Successful response: `201 Created`

The API generates an item ID and adds the item to the catalogue.

Customers attempting this operation receive `403 Forbidden`.

### 11.5 Delete Catalogue Item

**Method:** DELETE  
**Endpoint:** `/items/:id`  
**Authentication:** Required  
**Allowed role:** Restaurant

Example:

```text
DELETE /items/3
```

Successful response:

```text
204 No Content
```

The response body is empty.

Customers attempting this operation receive `403 Forbidden`.

## 12. Assignment Questions and Answers

### Q1. Which route(s) require only authentication, and which also require a role? Give the method + path and the role allowed for each.

**Answer:**

The `/login` route does not require authentication because users need to log in before obtaining a JWT.

The following routes require authentication only. Both Customer and Restaurant roles are allowed:

| Method | Path | Authentication | Allowed roles |
|---|---|---|---|
| GET | `/items` | Required | Customer, Restaurant |
| GET | `/items/:id` | Required | Customer, Restaurant |

The following routes require both authentication and role-based authorization. Only the Restaurant role is allowed:

| Method | Path | Authentication | Required role |
|---|---|---|---|
| POST | `/items` | Required | Restaurant |
| DELETE | `/items/:id` | Required | Restaurant |

The `requireRole('restaurant')` middleware checks the user's role after the authentication middleware verifies the JWT.

Therefore, customers can read catalogue information but cannot add or delete menu items.

### Q2. Show one 401 and one 403 from your demo. In one line each, say why the server returned that code (not the other).

**Answer:**

**401 Unauthorized —** `GET /items` without an Authorization token returned `401` because the request was not authenticated; the server could not verify the user's identity.

**403 Forbidden —** `POST /items` using a valid Customer token returned `403` because the user was authenticated but did not have the Restaurant role required to add menu items.

The difference is that `401` indicates missing or invalid authentication, whereas `403` indicates that an authenticated user lacks the required permission.

### Q3. What is inside your JWT payload? Why is it safe to trust the role claim on the server, and why must the secret stay out of your code?

**Answer:**

The JWT payload contains the user's ID and role, along with standard JWT claims such as issued-at (`iat`) and expiration (`exp`).

Example decoded payload:

```json
{
  "id": 2,
  "role": "restaurant",
  "iat": 1794228686,
  "exp": 1794232286
}
```

The `id` identifies the user, and the `role` specifies the user's permissions. The `iat` claim represents the token's issue time, and the `exp` claim represents its expiration time.

The server can trust the role claim only after successfully verifying the JWT signature using `jwt.verify()` and the server's secret. This verification confirms that the token was signed using the expected secret and has not been modified. The server must not trust a role sent separately by the client.

The JWT secret must remain outside the source code because anyone who obtains the secret could generate valid tokens and potentially impersonate users with privileged roles. Keeping the secret in the `.env` file and excluding that file from GitHub helps protect the application's authentication system.

## 13. Testing with Thunder Client

The API was tested using the Thunder Client extension in Visual Studio Code.

| Test | Request | Expected Result | Status |
|---|---|---|---|
| 1 | Restaurant login | 200 OK | Passed |
| 2 | GET `/items` without token | 401 Unauthorized | Passed |
| 3 | GET `/items` with valid token | 200 OK | Passed |
| 4 | Login with incorrect password | 401 Unauthorized | Passed |
| 5 | GET `/items/1` with valid token | 200 OK | Passed |
| 6 | GET `/items/999` with valid token | 404 Not Found | Passed |
| 7 | POST `/items` as restaurant | 201 Created | Passed |
| 8 | POST `/items` as customer | 403 Forbidden | Passed |
| 9 | DELETE `/items/3` as restaurant | 204 No Content | Passed |
| 10 | DELETE `/items/1` as customer | 403 Forbidden | Passed |

### Test Observations

- Authentication successfully rejects requests without a token.
- Valid JWT tokens allow access to protected read operations.
- Incorrect credentials are rejected.
- The restaurant role can add and delete catalogue items.
- The customer role cannot perform restricted write operations.
- Requests for non-existent catalogue items return `404 Not Found`.

All ten listed tests were completed successfully.

## 14. Security Features

The following security features are implemented:

1. **Password verification:** bcrypt is used to verify passwords.
2. **JWT authentication:** Tokens are generated after successful login.
3. **Token expiration:** JWT tokens expire after one hour.
4. **Protected routes:** Catalogue routes require authentication.
5. **Role-based access control:** Write operations are restricted to restaurant users.
6. **Environment configuration:** JWT secret is read from an environment variable.
7. **HTTP status codes:** Authentication, authorization, and resource errors are handled using appropriate status codes.

## 15. Environment and Git Configuration

The actual `.env` file contains the private JWT secret and must not be committed.

The `.env.example` file provides a configuration template.

Example:

```env
JWT_SECRET=
```

The `.gitignore` file should contain:

```gitignore
node_modules/
.env
```

This prevents installed dependencies and private environment configuration from being included in the repository.

## 16. Running the Application

To run the application locally:

```bash
npm install
```

Configure the `.env` file.

Then execute:

```bash
node server.js
```

Open:

```text
http://localhost:3000
```

Use Thunder Client to test the API endpoints.

## 17. Conclusion

Assignment 09 extends the CampusEats Catalogue API developed in Assignment 08 by implementing authentication and role-based authorization.

The application uses bcrypt for password verification and JWT for authentication. Middleware protects API routes and restricts write operations according to user roles.

Testing with Thunder Client demonstrated that the API correctly handles valid and invalid credentials, missing tokens, protected read operations, restricted write operations, and requests for non-existent items.

The assignment demonstrates the implementation of basic security mechanisms in a RESTful web service using Node.js and Express.js.

## 18. Submission Links

**GitHub Repository:**  
[Add your GitHub repository link here]

**Google Drive Demo Video:**  
https://drive.google.com/file/d/1_LbcZxRt12DkB6UpLnEwsosLefB6HN4u/view?usp=sharing

**Screenshots:**  
Include screenshots of the Thunder Client testing results in the submission folder.
