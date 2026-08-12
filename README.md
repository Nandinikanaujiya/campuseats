# CampusEats - CS 543 Web Services Assignments

This repository contains the assignments and design documentation for CS 543 Web Services.

## Contents

### Assignment 1
- **[docs/http-log.md](docs/http-log.md)** - Log of HTTP request and response analysis using curl.
- **[docs/network-analysis.md](docs/network-analysis.md)** - Browser DevTools network analysis report of github.com.
- **[docs/brief.md](docs/brief.md)** - Overview and brief of the CampusEats system.

### Assignment 2
- **[design.pdf](design.pdf)** - Capabilities list, service contracts, placeOrder specification, and service properties validation table.
- **[services.drawio](services.drawio)** / **[services.png](services.png)** - Service design diagram showing microservice boundaries.
- **[schema.drawio](schema.drawio)** / **[schema.png](schema.png)** - Database ER diagram for the services.
- **[schema.sql](schema.sql)** - Database table creation queries grouped by service boundaries.

## Verification
- HTTP calls can be reproduced with standard `curl` commands shown in the logs.
- Network analytics were captured using Chrome DevTools with no caching.
- Diagrams are editable XML source files that can be opened in draw.io (diagrams.net).
