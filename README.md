# CampusEats Engineering & Analysis Suite

[![Web Services](https://img.shields.io/badge/Course-CS%20543%20Web%20Services-blue.svg)](https://github.com/TargetUltimate-Alka/campuseats)
[![Author](https://img.shields.io/badge/Author-Radhika%20Verma-orange.svg)](https://github.com/Radhika-Verma08)
[![Documentation](https://img.shields.io/badge/Documentation-Complete-brightgreen.svg)]()

### 👥 Team & Members (Team No. 10)
* **Nandini Kanaujiya** - `20251651061`
* **Radhika Verma** - `20251651075`
* **Alka Jha** - `20251651013`
* **Alok Mishra** - `20251651014`

---

Welcome to the **CampusEats Engineering & Analysis Suite**. This repository contains the complete deliverables for **Assignment 1 & Assignment 2 of CS 543 Web Services**. It covers HTTP diagnostics, browser network profiling, and a comprehensive architectural system design brief for a campus food delivery network (Assignment 1), as well as microservice architecture and database schemas (Assignment 2).

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

## 🛠️ Verification & Tools Used

To replicate or verify the logs in this repository:
- **HTTP Requests:** Run standard `curl` commands in a terminal:
  ```bash
  curl -i https://jsonplaceholder.typicode.com/users/1
  ```
- **Network Profiling:** Open Google Chrome Developer Tools (`Ctrl+Shift+I` or `F12`), head to the **Network** tab, check **Disable Cache**, and reload (`Ctrl+R`).
- **Diagrams:** Markdown files use **Draw.io** diagrams for rendering database schema and system architecture directly within Markdown viewers.
