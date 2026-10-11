# CampusEats Engineering & Analysis Suite

[![Web Services](https://img.shields.io/badge/Course-CS%20543%20Web%20Services-blue.svg)](https://github.com/TargetUltimate-Alka/campuseats)
[![Author](https://img.shields.io/badge/Author-Nandini%20Kanaujiya-orange.svg)](https://github.com/Nandinikanaujiya)
[![Documentation](https://img.shields.io/badge/Documentation-Complete-brightgreen.svg)]()

### 👥 Team & Members (Team No. 11)
// changed the team no : 10->11
* **Nandini Kanaujiya** - `20251651061`
* **Radhika Verma** - `20251651075`
* **Alka Jha** - `20251651013`
* **Alok Mishra** - `20251651014`

---

Welcome to the **CampusEats Engineering & Analysis Suite**. This repository contains the complete deliverables for **Assignments 1, 2, 3, 4, 5, and 6 of CS 543 Web Services**. It covers HTTP diagnostics (Assignment 1), microservice architecture and schemas (Assignment 2), SOAP partner integration (Assignment 3), rebuilding the Orders service in REST (Assignment 4), HTTP methods and headers (Assignment 5), and honest responses, status codes, RFC 7807 problem details, and multi-field validation (Assignment 6).

---

## 📂 Repository Contents

### 📝 Assignment 1

The assignment is divided into three key engineering components:

#### 1. 🛠️ [HTTP Request/Response Diagnostics](docs/http-log.md)
* **File:** [docs/http-log.md](file:///C:/AI%20Coding%20Challenge%20Platform/docs/http-log.md)
* **Overview:** Complete raw log of REST API requests (GET, POST, PUT, and error handling) against the JSONPlaceholder API.
* **Key Details:** Annotated analysis of HTTP headers including caching (`Cache-Control`), MIME-types (`Content-Type`), compression status, and rate-limiting (`X-Ratelimit`).

#### 2. 📊 [Browser DevTools Network Profile](docs/network-analysis.md)
* **File:** [docs/network-analysis.md](file:///C:/AI%20Coding%20Challenge%20Platform/docs/network-analysis.md)
* **Overview:** A deep-dive network profiling of the GitHub desktop homepage.
* **Key Details:** Logs total network metrics (requests, transferred size, page load times) and lists critical optimization paths (code-splitting, lazy-loading, caching headers) to fix bottleneck resources.

#### 3. 🍔 [CampusEats System Architectural Brief](docs/brief.md)
* **File:** [docs/brief.md](file:///C:/AI%20Coding%20Challenge%20Platform/docs/brief.md)
* **Overview:** A comprehensive engineering brief outlining the system structure, entities, and database design for the **CampusEats** platform.
* **Key Details:** Contains user role definitions, a Draw.io-powered Entity Relationship (ER) database diagram, core REST API contracts, and real-time synchronization workflows.

---

### 🚀 Assignment 2

This section contains the deliverables and design benchmark for Assignment 2:

#### 1. 📋 [Service Design & Contracts](campuseats-assignment2/design.pdf)
* **File:** [campuseats-assignment2/design.pdf](file:///C:/AI%20Coding%20Challenge%20Platform/campuseats-assignment2/design.pdf)
* **Overview:** Capabilities list, service contracts, `placeOrder` detailed specification, and service validation property table.

#### 2. 🎨 [Service Architecture Mapping](campuseats-assignment2/services.drawio)
* **File:** [campuseats-assignment2/services.drawio](file:///C:/AI%20Coding%20Challenge%20Platform/campuseats-assignment2/services.drawio) (Editable Draw.io) / [campuseats-assignment2/services.png](file:///C:/AI%20Coding%20Challenge%20Platform/campuseats-assignment2/services.png) (Image)
* **Overview:** Service design mapping service boundaries, data ownership, and inter-service call operations.

#### 3. 🗄️ [Database Entity Relationship Diagram](campuseats-assignment2/schema.drawio)
* **File:** [campuseats-assignment2/schema.drawio](file:///C:/AI%20Coding%20Challenge%20Platform/campuseats-assignment2/schema.drawio) (Editable Draw.io) / [campuseats-assignment2/schema.png](file:///C:/AI%20Coding%20Challenge%20Platform/campuseats-assignment2/schema.png) (Image)
* **Overview:** Database ERD defining private schemas and cross-boundary references.

#### 4. 🗃️ [DDL Queries](campuseats-assignment2/schema.sql)
* **File:** [campuseats-assignment2/schema.sql](file:///C:/AI%20Coding%20Challenge%20Platform/campuseats-assignment2/schema.sql)
* **Overview:** Database table creation queries (DDL) for PostgreSQL grouped by service schema limits.

---

### 🔌 Assignment 3

This section contains the SOAP Partner Integration design deliverables for Assignment 3:

#### 1. 📄 [Integration Report](Assignment-3/integration.pdf)
* **File:** [Assignment-3/integration.pdf](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-3/integration.pdf)
* **Overview:** Detailed brief covering context/justification for SOAP, HTTP binding details, modern service discovery/registry entry, and SOAP-to-REST fault mapping.

#### 2. 📜 [Partner WSDL Contract](Assignment-3/partner.wsdl)
* **File:** [Assignment-3/partner.wsdl](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-3/partner.wsdl)
* **Overview:** Web Service Description Language (WSDL 1.1) contract for the external `SecurePay` service.

#### 3. ✉️ SOAP Messages
* **Files:**
  - [soap-request.xml](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-3/soap-request.xml) &mdash; Hand-formed SOAP Request with WS-Security header.
  - [soap-response.xml](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-3/soap-response.xml) &mdash; Hand-formed SOAP success Response envelope.
  - [soap-fault.xml](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-3/soap-fault.xml) &mdash; SOAP Fault envelope representing card declination/insufficient funds.

---

### 🌐 Assignment 4

This section contains the RESTful Rebuilding of the CampusEats Orders Service:

#### 1. 📑 [OpenAPI 3.0 Contract](Assignment-4/openapi.yaml)
* **File:** [Assignment-4/openapi.yaml](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/openapi.yaml)
* **Overview:** Complete OpenAPI 3.0.3 specification covering all order operations, parameters, reusable schemas, and RFC 7807 error responses.

#### 2. 💻 Microservice Implementation
* **Files:**
  - [app.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/app.py) &mdash; Flask route handlers (`POST /orders`, `GET /orders/<id>`, `GET /orders`, `POST /orders/<id>/cancellation`).
  - [models.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/models.py) &mdash; Domain model, manual validation, and clean representation separation (`as_json()`).
  - [store.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/store.py) &mdash; In-memory data store and idempotency cache.
  - [client.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/client.py) &mdash; Hardened outbound payment client (timeout, exponential backoff, jitter, safe retries).
  - [errors.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/errors.py) &mdash; Uniform RFC 7807 `problem()` helper.

#### 3. 🧪 [Automated Tests](Assignment-4/tests/test_orders.py)
* **File:** [Assignment-4/tests/test_orders.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/tests/test_orders.py)
* **Overview:** Pytest test suite covering successful creation with Location header, idempotent repeats, failure 4xx codes, and 404 lookups.

#### 4. 📝 [Assignment Report & Notes](Assignment-4/NOTES.md)
* **File:** [Assignment-4/NOTES.md](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-4/NOTES.md)
* **Overview:** Comprehensive technical report covering Resource Table, A5 justification, D3 fallback reasoning, answers to Questions 1–5, and complete live `curl -i` transcript.

---

### 📡 Assignment 5

This section contains HTTP Methods & Headers implementation for the CampusEats Orders Service:

#### 1. 📑 [OpenAPI 3.0 Contract](Assignment-5/openapi.yaml)
* **File:** [Assignment-5/openapi.yaml](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-5/openapi.yaml)
* **Overview:** Complete OpenAPI specification with conditional requests (ETag / If-None-Match, If-Match), CORS, and rate limiting headers.

#### 2. 💻 Microservice Implementation
* **Files:**
  - [app.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-5/app.py) &mdash; Orders service with conditional caching (`304 Not Modified`), optimistic concurrency (`412 Precondition Failed`), `OPTIONS` verb discovery, and `X-HTTP-Method-Override`.
  - [models.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-5/models.py) &mdash; ETag computation (`compute_etag()`), versioning, and state replacement.
  - [store.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-5/store.py) &mdash; In-memory store and sliding window rate limiter.
  - [client.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-5/client.py) &mdash; Resilient payment client with simulation modes.

#### 3. 🧪 [Automated Tests](Assignment-5/tests/test_orders.py)
* **File:** [Assignment-5/tests/test_orders.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-5/tests/test_orders.py)
* **Overview:** 14 automated pytest cases verifying conditional GET/PUT, idempotency, rate limiting, and verb discovery.

#### 4. 📝 [Assignment Report & Notes](Assignment-5/NOTES.md)
* **File:** [Assignment-5/NOTES.md](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-5/NOTES.md)
* **Overview:** Detailed technical documentation answering all Assignment 5 questions and including full verified curl transcripts.

---

### 🛡️ Assignment 6

This section contains the deliverables for **Assignment 6: Honest responses: status codes, errors & validation**:

#### 1. 📑 [OpenAPI 3.0 Contract](Assignment-6/openapi.yaml)
* **File:** [Assignment-6/openapi.yaml](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/openapi.yaml)
* **Overview:** OpenAPI 3.0.3 specification covering all status codes, RFC 7807/9457 Problem Details schemas, field-level 422 error structures, and Content Negotiation.

#### 2. 💻 Microservice Implementation
* **Files:**
  - [app.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/app.py) &mdash; Orders service with comprehensive status code mapping, multi-field validation, content negotiation (`application/json` & `application/xml`, `406 Not Acceptable`), `Retry-After` headers, and internal error concealment.
  - [models.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/models.py) &mdash; Order domain model with XML (`to_xml()`) and JSON serialization, state machine checks.
  - [schema.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/schema.py) &mdash; JSON Schema and multi-error validator collecting all bad fields simultaneously.
  - [errors.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/errors.py) &mdash; RFC 7807 Problem Details builder supporting JSON and XML with explicit `charset=utf-8`.
  - [store.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/store.py) &mdash; In-memory store, sliding window rate limiter, outage simulator.
  - [client.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/client.py) &mdash; Payment and inventory stock client with failure mode simulations.

#### 3. 🧪 [Automated Tests](Assignment-6/tests/test_orders.py)
* **File:** [Assignment-6/tests/test_orders.py](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/tests/test_orders.py)
* **Overview:** 16 automated pytest cases verifying status codes, multi-error 422, XML negotiation, rate limiting, and A5 regressions.

#### 4. 📜 [Live curl Transcript](Assignment-6/transcript.txt)
* **File:** [Assignment-6/transcript.txt](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/transcript.txt) / [Assignment-6/curl-transcript.txt](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/curl-transcript.txt)
* **Overview:** Live captured curl -i sessions proving happy path (D1), failure paths (D2), content negotiation (D3), and regression checks (D4).

#### 5. 📝 [Assignment Report & Notes](Assignment-6/NOTES.md)
* **File:** [Assignment-6/NOTES.md](file:///C:/AI%20Coding%20Challenge%20Platform/Assignment-6/NOTES.md)
* **Overview:** Complete technical report answering Questions 1–7 with Team 11 member details.

---

## 🛠️ Verification & Tools Used

To replicate or verify the logs in this repository:
- **HTTP Requests:** Run standard `curl` commands in a terminal:
  ```bash
  curl -i https://jsonplaceholder.typicode.com/users/1
  ```
- **Network Profiling:** Open Google Chrome Developer Tools (`Ctrl+Shift+I` or `F12`), head to the **Network** tab, check **Disable Cache**, and reload (`Ctrl+R`).
- **Diagrams:** Markdown files use **Draw.io** diagrams for rendering database schema and system architecture directly within Markdown viewers.
