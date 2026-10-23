
-- 1. Create the database
CREATE DATABASE IF NOT EXISTS gqldemo;
USE gqldemo;

-- 2. Create the authors table
CREATE TABLE authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50)
);

-- 3. Create the books table
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    year INT,
    author_id INT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- 4. Insert sample authors
INSERT INTO authors (name, country) VALUES
('Asha Patel', 'India'),
('Ravi Kumar', 'India');

-- 5. Insert sample books
INSERT INTO books (title, year, author_id) VALUES
('Databases 101', 2020, 1),
('SQL in Practice', 2022, 1),
('Web Services Basics', 2023, 2);
