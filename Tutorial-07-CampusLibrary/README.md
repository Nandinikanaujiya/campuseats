# Campus Library — GraphQL Tutorial

## Team details - Team Number 11 

- Alka Jha - 20251651013
- Alok Mishra - 20251651014
- Nandini Kanaujiya - 20251651061
- Radhika Verma - 20251651075

## 1. Overview

This project demonstrates a basic GraphQL API for a Campus Library system. It uses Node.js, Apollo Server, GraphQL, and MySQL to retrieve and manage library data.

## 2. Technologies Used

- Node.js
- Apollo Server
- GraphQL
- MySQL
- mysql2
- dotenv
- HTML, CSS, and JavaScript

## 3. Project Structure

```text
campus-library/
├── public/
├── .env.example
├── .gitignore
├── db.js
├── package.json
├── package-lock.json
├── schema.sql
├── server.js
└── README.md
```

## 4. Prerequisites

Install the following before running the project:

- Node.js and npm
- MySQL Server

## 5. Setup Instructions

### Step 1: Install dependencies

```bash
npm install
```

If `dotenv` is not installed, run:

```bash
npm install dotenv
```

### Step 2: Create the database

Run the SQL script in `schema.sql` using MySQL.

For example, in PowerShell:

```powershell
Get-Content .\schema.sql -Raw | & "D:\This pc\mysql\bin\mysql.exe" -u root -p
```

Adjust the MySQL executable path if it differs on your computer.

### Step 3: Configure environment variables

Create a local `.env` file in the project root using `.env.example` as a reference.

Set your MySQL credentials:

```dotenv
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=gqldemo
```

Replace the password placeholder with your local MySQL password. If your MySQL account has no password, use `DB_PASSWORD=`.

**Security:** Never commit `.env` or your database password to GitHub.

### Step 4: Start the server

Run:

```bash
node server.js
```

Use the GraphQL endpoint and port configured in `server.js`.

## 6. GraphQL API

The API exposes the operations defined in the project's GraphQL schema. Use the queries and mutations actually implemented in `server.js` and `schema.graphql`.

## 7. GitHub Repository

Repository: [CampusEats](https://github.com/Nandinikanaujiya/campuseats)

Tutorial folder: `Tutorial-07-CampusLibrary/`

## 8. Demonstration

Demonstration Video:
[https://drive.google.com/file/d/1uBrDGW4RDRrS_6zCieDD1QDVs18oko8N/view?usp=sharing]

## 9. Screenshots

screenshots folder contain the before and after mutation snapshots.
