# CampusEats Engineering & Analysis Suite

[![Web Services](https://img.shields.io/badge/Course-CS%20543%20Web%20Services-blue.svg)](https://github.com/TargetUltimate-Alka/campuseats)
[![Assignment](https://img.shields.io/badge/Task-Assignment%201-orange.svg)]()
[![Documentation](https://img.shields.io/badge/Documentation-Complete-brightgreen.svg)]()

Welcome to the **CampusEats Engineering & Analysis Suite**. This repository contains the complete deliverables for **Assignment 1 of CS 543 Web Services**. It covers hands-on HTTP diagnostics, browser network profiling, and a comprehensive architectural system design brief for a campus food delivery network.

---

## 📂 Repository Contents

The assignment is divided into three key engineering components:

### 1. 🛠️ [HTTP Request/Response Diagnostics](docs/http-log.md)
* **File:** [docs/http-log.md](file:///C:/AI%20Coding%20Challenge%20Platform/docs/http-log.md)
* **Overview:** Complete raw log of REST API requests (GET, POST, PUT, and error handling) against the JSONPlaceholder API.
* **Key Details:** Annotated analysis of HTTP headers including caching (`Cache-Control`), MIME-types (`Content-Type`), compression status, and rate-limiting (`X-Ratelimit`).

### 2. 📊 [Browser DevTools Network Profile](docs/network-analysis.md)
* **File:** [docs/network-analysis.md](file:///C:/AI%20Coding%20Challenge%20Platform/docs/network-analysis.md)
* **Overview:** A deep-dive network profiling of the GitHub desktop homepage.
* **Key Details:** Logs total network metrics (requests, transferred size, page load times) and lists critical optimization paths (code-splitting, lazy-loading, caching headers) to fix bottleneck resources.

### 3. 🍔 [CampusEats System Architectural Brief](docs/brief.md)
* **File:** [docs/brief.md](file:///C:/AI%20Coding%20Challenge%20Platform/docs/brief.md)
* **Overview:** A comprehensive engineering brief outlining the system structure, entities, and database design for the **CampusEats** platform.
* **Key Details:** Contains user role definitions, a Mermaid-powered Entity Relationship (ER) database diagram, core REST API contracts, and real-time synchronization workflows.

---

## 🛠️ Verification & Tools Used

To replicate or verify the logs in this repository:
- **HTTP Requests:** Run standard `curl` commands in a terminal:
  ```bash
  curl -i https://jsonplaceholder.typicode.com/users/1
  ```
- **Network Profiling:** Open Google Chrome Developer Tools (`Ctrl+Shift+I` or `F12`), head to the **Network** tab, check **Disable Cache**, and reload (`Ctrl+R`).
- **Diagrams:** Markdown files use **MermaidJS** syntax for rendering database diagrams directly within GitHub or compatible markdown viewers.
