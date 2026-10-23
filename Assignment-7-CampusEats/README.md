# CampusEats — GraphQL Menu Service

## Team Members

- Alka Jha - 20251651013
- Alok Mishra - 20251651014
- Nandini Kanaujiya - 20251651061
- Radhika Verma - 20251651075

## 1. Service Selected

We selected the Menu/Dishes service of CampusEats.
It exposes dish information through a GraphQL API backed by MySQL.

## 2. Technology Stack

- Node.js
- Apollo Server
- GraphQL
- MySQL
- mysql2
- HTML and CSS

## 3. GraphQL Operations

- Query: dishes — lists all dishes.
- Query: dish(id) — fetches a dish by ID.
- Mutation: addDish(input) — inserts a new dish.

## 4. Understanding the ! Sign

The exclamation mark indicates a non-null field or argument.
For example, name: String! means the name cannot be null.
An optional field can be omitted where the schema permits it.

## 5. GraphQL to SQL Mapping

The dish(id) resolver uses the GraphQL ID argument in a SQL
WHERE clause: WHERE id = ?.

The addDish resolver executes an SQL INSERT statement to
create a new dish in the database.

## 6. How to Run

1. Install Node.js and MySQL.
2. Run schema.sql in MySQL.
3. Configure the MySQL credentials in db.js.
4. Install dependencies with npm install.
5. Start the server using node server.js.
6. Open public/index.html with VS Code Live Server.

## 7. Demonstration

GitHub Repository:
[https://github.com/Nandinikanaujiya/campuseats/tree/main/Assignment-7-CampusEats]

Demonstration Video:
[https://drive.google.com/file/d/1WQsEJicNojdKtAjWpXVCoCnz1vA5I6VT/view?usp=sharing]

Screenshots:
See the screenshots folder.
