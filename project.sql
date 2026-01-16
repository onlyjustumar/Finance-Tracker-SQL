
DROP DATABASE IF EXISTS finance_management;
CREATE DATABASE finance_management;
USE finance_management;



-- Users Table
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Categories Table
CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    user_id INT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Incomes Table
CREATE TABLE incomes (
    income_id INT PRIMARY KEY,
    user_id INT,
    source VARCHAR(100),
    category_id INT,
    amount DECIMAL(10,2) NOT NULL,
    income_date DATE,
    note TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

-- Expenses Table
CREATE TABLE expenses (
    expense_id INT PRIMARY KEY,
    user_id INT,
    category_id INT,
    amount DECIMAL(10,2) NOT NULL,
    expense_date DATE,
    note TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

-- Budgets Table
CREATE TABLE budgets (
    budget_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    category_id INT,
    limit_amount DECIMAL(10,2) NOT NULL,
    start_date DATE,
    end_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);



INSERT INTO users VALUES
(1, 'Muhammad Umar Ramzan', 'umar@gmail.com', '123');

INSERT INTO categories VALUES
(1, 1, 'Groceries', 'Food and household items'),
(2, 1, 'Transport', 'Bus, taxi, fuel'),
(3, 1, 'Salary', 'Monthly income');

INSERT INTO incomes VALUES
(1, 1, 'ABC Company', 3, 50000.00, '2025-11-01', 'November Salary');

INSERT INTO expenses VALUES
(1, 1, 1, 1500.00, '2025-11-05', 'Groceries shopping'),
(2, 1, 2, 200.00, '2025-11-06', 'Office transport');

INSERT INTO budgets (user_id, category_id, limit_amount, start_date, end_date)
VALUES (1, 1, 10000.00, '2025-11-01', '2025-11-30');




SELECT u.name, c.name AS category, e.amount, e.expense_date
FROM users u
JOIN expenses e ON u.user_id = e.user_id
JOIN categories c ON e.category_id = c.category_id;


SELECT c.name, e.amount
FROM categories c
LEFT JOIN expenses e ON c.category_id = e.category_id;




SELECT user_id, SUM(amount) AS total_income
FROM incomes
GROUP BY user_id;


SELECT category_id, SUM(amount) AS total_expense
FROM expenses
GROUP BY category_id;


SELECT AVG(amount) AS average_expense
FROM expenses;




SELECT *
FROM expenses
WHERE amount > (
    SELECT AVG(amount) FROM expenses
);



SELECT name
FROM categories
WHERE category_id IN (
    SELECT category_id
    FROM expenses
    GROUP BY category_id
    HAVING SUM(amount) > 1000
);




SELECT *
FROM expenses e
WHERE amount > (
    SELECT AVG(amount)
    FROM expenses
    WHERE user_id = e.user_id
);




SELECT *
FROM expenses
WHERE amount > ANY (
    SELECT amount
    FROM expenses
    WHERE category_id = 2
);


SELECT *
FROM expenses
WHERE amount > ALL (
    SELECT amount
    FROM expenses
    WHERE category_id = 2
);



-- Budget vs actual expenses
SELECT c.name AS category,
       b.limit_amount,
       SUM(e.amount) AS total_spent,
       (b.limit_amount - SUM(e.amount)) AS remaining_budget
FROM budgets b
JOIN categories c ON b.category_id = c.category_id
JOIN expenses e ON b.category_id = e.category_id
GROUP BY b.category_id;



-- Categories exceeding budget
SELECT name
FROM categories
WHERE category_id IN (
    SELECT b.category_id
    FROM budgets b
    JOIN expenses e ON b.category_id = e.category_id
    GROUP BY b.category_id
    HAVING SUM(e.amount) > b.limit_amount
);
