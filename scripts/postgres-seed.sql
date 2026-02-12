-- BIAI Test Database Seed - PostgreSQL
-- 6 business tables with realistic data

-- ============================================================
-- 1. SALES_REGIONS (~10 rows)
-- ============================================================
CREATE TABLE sales_regions (
    region_id   SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    country     VARCHAR(100) NOT NULL,
    manager     VARCHAR(100)
);

INSERT INTO sales_regions (region_name, country, manager) VALUES
    ('North America East', 'USA', 'John Mitchell'),
    ('North America West', 'USA', 'Sarah Chen'),
    ('Europe Central', 'Germany', 'Klaus Weber'),
    ('Europe South', 'Spain', 'Maria Garcia'),
    ('Europe North', 'Sweden', 'Erik Johansson'),
    ('Asia Pacific', 'Japan', 'Takeshi Yamamoto'),
    ('South America', 'Brazil', 'Carlos Silva'),
    ('Middle East', 'UAE', 'Ahmed Al-Rashid'),
    ('Africa', 'South Africa', 'Thandi Nkosi'),
    ('Oceania', 'Australia', 'James Cook');

-- ============================================================
-- 2. CUSTOMERS (~100 rows)
-- ============================================================
CREATE TABLE customers (
    customer_id   SERIAL PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(200) UNIQUE NOT NULL,
    city          VARCHAR(100),
    country       VARCHAR(100),
    segment       VARCHAR(50) CHECK (segment IN ('Enterprise', 'SMB', 'Startup', 'Government')),
    region_id     INT REFERENCES sales_regions(region_id),
    created_at    TIMESTAMP DEFAULT NOW()
);

INSERT INTO customers (first_name, last_name, email, city, country, segment, region_id, created_at)
SELECT
    (ARRAY['James','Mary','Robert','Patricia','John','Jennifer','Michael','Linda','David','Elizabeth',
           'William','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Charles','Karen',
           'Christopher','Lisa','Daniel','Nancy','Matthew','Betty','Anthony','Margaret','Mark','Sandra',
           'Donald','Ashley','Steven','Kimberly','Paul','Emily','Andrew','Donna','Joshua','Michelle',
           'Kenneth','Carol','Kevin','Amanda','Brian','Dorothy','George','Melissa','Timothy','Deborah',
           'Anna','Maria','Elena','Sofia','Yuki','Mei','Priya','Fatima','Olga','Ingrid',
           'Hans','Pierre','Marco','Pedro','Ali','Chen','Raj','Omar','Igor','Lars'])[floor(random()*70+1)::int],
    (ARRAY['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez',
           'Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin',
           'Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson',
           'Walker','Young','Allen','King','Wright','Scott','Torres','Nguyen','Hill','Flores',
           'Green','Adams','Nelson','Baker','Hall','Rivera','Campbell','Mitchell','Carter','Roberts',
           'Weber','Mueller','Schmidt','Fischer','Yamamoto','Tanaka','Kumar','Singh','Ivanov','Petrov'])[floor(random()*60+1)::int],
    'user' || i || '_' || substr(md5(random()::text), 1, 6) || '@example.com',
    (ARRAY['New York','Los Angeles','Chicago','Houston','Phoenix','San Francisco','Seattle','Denver',
           'Berlin','Munich','Madrid','Barcelona','Stockholm','Tokyo','Osaka','Sao Paulo',
           'Dubai','Johannesburg','Sydney','Melbourne','London','Paris','Rome','Toronto','Vancouver'])[floor(random()*25+1)::int],
    (ARRAY['USA','USA','USA','USA','USA','USA','USA','USA',
           'Germany','Germany','Spain','Spain','Sweden','Japan','Japan','Brazil',
           'UAE','South Africa','Australia','Australia','UK','France','Italy','Canada','Canada'])[floor(random()*25+1)::int],
    (ARRAY['Enterprise','SMB','Startup','Government'])[floor(random()*4+1)::int],
    floor(random()*10+1)::int,
    NOW() - (random() * INTERVAL '730 days')
FROM generate_series(1, 100) AS s(i);

-- ============================================================
-- 3. PRODUCTS (~50 rows)
-- ============================================================
CREATE TABLE products (
    product_id   SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category     VARCHAR(100) NOT NULL,
    unit_price   NUMERIC(10,2) NOT NULL,
    cost_price   NUMERIC(10,2) NOT NULL
);

INSERT INTO products (product_name, category, unit_price, cost_price)
SELECT
    name,
    category,
    price,
    ROUND(price * (0.4 + random() * 0.3)::numeric, 2)
FROM (VALUES
    ('Enterprise Analytics Suite', 'Software', 4999.99),
    ('Cloud Data Warehouse License', 'Software', 2499.99),
    ('BI Dashboard Pro', 'Software', 1299.99),
    ('Data Integration Platform', 'Software', 3499.99),
    ('ML Model Server', 'Software', 5999.99),
    ('Real-time Streaming Engine', 'Software', 1999.99),
    ('API Gateway Premium', 'Software', 899.99),
    ('Security Compliance Module', 'Software', 1499.99),
    ('DevOps Pipeline Toolkit', 'Software', 799.99),
    ('Database Optimizer Pro', 'Software', 1199.99),
    ('Rack Server RS-4000', 'Hardware', 12999.99),
    ('Rack Server RS-2000', 'Hardware', 7999.99),
    ('Storage Array SA-500', 'Hardware', 24999.99),
    ('Network Switch NS-48', 'Hardware', 3499.99),
    ('GPU Compute Node GC-8', 'Hardware', 18999.99),
    ('Edge Computing Device', 'Hardware', 2499.99),
    ('SSD Module 4TB', 'Hardware', 899.99),
    ('RAM Module 128GB', 'Hardware', 649.99),
    ('Fiber Optic Cable Kit', 'Hardware', 299.99),
    ('UPS Power Unit 3000VA', 'Hardware', 1899.99),
    ('24/7 Premium Support', 'Services', 4999.99),
    ('Implementation Consulting', 'Services', 14999.99),
    ('Data Migration Service', 'Services', 9999.99),
    ('Staff Training Program', 'Services', 2999.99),
    ('Architecture Review', 'Services', 7499.99),
    ('Performance Tuning', 'Services', 5999.99),
    ('Security Audit', 'Services', 8999.99),
    ('Disaster Recovery Setup', 'Services', 11999.99),
    ('Custom Integration', 'Services', 19999.99),
    ('Managed Database Service', 'Services', 3499.99),
    ('Basic Support Plan', 'Subscription', 99.99),
    ('Professional Plan', 'Subscription', 299.99),
    ('Enterprise Plan', 'Subscription', 999.99),
    ('Data Lake Storage 1TB', 'Subscription', 149.99),
    ('Data Lake Storage 10TB', 'Subscription', 999.99),
    ('API Calls - 1M/month', 'Subscription', 49.99),
    ('API Calls - 10M/month', 'Subscription', 399.99),
    ('Monitoring & Alerting', 'Subscription', 199.99),
    ('Log Analytics 100GB', 'Subscription', 249.99),
    ('Backup Service Premium', 'Subscription', 179.99),
    ('IoT Sensor Pack S', 'Hardware', 499.99),
    ('IoT Sensor Pack M', 'Hardware', 1299.99),
    ('IoT Sensor Pack L', 'Hardware', 2999.99),
    ('AI Training Bootcamp', 'Services', 4499.99),
    ('Compliance Report Generator', 'Software', 699.99),
    ('ETL Pipeline Builder', 'Software', 1599.99),
    ('Data Quality Scanner', 'Software', 899.99),
    ('Report Designer', 'Software', 599.99),
    ('Mobile Analytics App', 'Software', 399.99),
    ('Embedded BI SDK', 'Software', 2999.99)
) AS v(name, category, price);

-- ============================================================
-- 4. EMPLOYEES (~30 rows)
-- ============================================================
CREATE TABLE employees (
    employee_id  SERIAL PRIMARY KEY,
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100) NOT NULL,
    department   VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    hire_date    DATE NOT NULL,
    salary       NUMERIC(10,2) NOT NULL,
    region_id    INT REFERENCES sales_regions(region_id)
);

INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES
    ('Alice', 'Morgan', 'Sales', 'VP of Sales', '2019-03-15', 145000.00, 1),
    ('Bob', 'Chen', 'Sales', 'Sales Director', '2020-01-10', 120000.00, 2),
    ('Carol', 'Weber', 'Sales', 'Sales Director', '2019-07-22', 118000.00, 3),
    ('David', 'Garcia', 'Sales', 'Account Executive', '2021-04-05', 85000.00, 4),
    ('Eva', 'Johansson', 'Sales', 'Account Executive', '2021-09-18', 82000.00, 5),
    ('Frank', 'Yamamoto', 'Sales', 'Account Executive', '2022-02-14', 80000.00, 6),
    ('Grace', 'Silva', 'Sales', 'Sales Rep', '2022-06-01', 65000.00, 7),
    ('Henry', 'Al-Rashid', 'Sales', 'Sales Rep', '2023-01-09', 63000.00, 8),
    ('Irene', 'Nkosi', 'Sales', 'Sales Rep', '2023-05-20', 60000.00, 9),
    ('Jack', 'Cook', 'Sales', 'Sales Rep', '2023-08-11', 62000.00, 10),
    ('Kate', 'Thompson', 'Engineering', 'CTO', '2018-11-01', 175000.00, 1),
    ('Liam', 'Nguyen', 'Engineering', 'Senior Engineer', '2020-03-15', 135000.00, 2),
    ('Maya', 'Petrov', 'Engineering', 'Senior Engineer', '2020-06-22', 130000.00, 3),
    ('Noah', 'Kumar', 'Engineering', 'Engineer', '2021-08-10', 105000.00, 6),
    ('Olivia', 'Fischer', 'Engineering', 'Engineer', '2022-01-15', 100000.00, 3),
    ('Peter', 'Brown', 'Engineering', 'Junior Engineer', '2023-04-01', 78000.00, 1),
    ('Quinn', 'Davis', 'Marketing', 'VP of Marketing', '2019-05-10', 140000.00, 1),
    ('Rachel', 'Martinez', 'Marketing', 'Marketing Manager', '2020-09-14', 95000.00, 4),
    ('Sam', 'Wilson', 'Marketing', 'Content Specialist', '2022-03-22', 70000.00, 1),
    ('Tina', 'Lee', 'Marketing', 'Digital Marketing', '2022-11-07', 72000.00, 6),
    ('Uma', 'Patel', 'Support', 'Support Director', '2019-08-19', 110000.00, 6),
    ('Victor', 'Santos', 'Support', 'Support Engineer', '2021-02-28', 75000.00, 7),
    ('Wendy', 'Mueller', 'Support', 'Support Engineer', '2021-10-15', 73000.00, 3),
    ('Xavier', 'Torres', 'Support', 'Support Analyst', '2023-02-01', 58000.00, 4),
    ('Yara', 'Kim', 'Finance', 'CFO', '2018-09-01', 165000.00, 1),
    ('Zach', 'Anderson', 'Finance', 'Financial Analyst', '2021-05-17', 88000.00, 1),
    ('Amy', 'Robinson', 'Finance', 'Accountant', '2022-07-10', 72000.00, 1),
    ('Ben', 'White', 'HR', 'HR Director', '2019-12-01', 115000.00, 1),
    ('Chloe', 'Harris', 'HR', 'HR Specialist', '2022-04-18', 68000.00, 1),
    ('Derek', 'Clark', 'Operations', 'COO', '2018-06-15', 155000.00, 1);

-- ============================================================
-- 5. ORDERS (~500 rows)
-- ============================================================
CREATE TABLE orders (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INT NOT NULL REFERENCES customers(customer_id),
    employee_id  INT REFERENCES employees(employee_id),
    order_date   DATE NOT NULL,
    status       VARCHAR(20) CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    total_amount NUMERIC(12,2) DEFAULT 0
);

INSERT INTO orders (customer_id, employee_id, order_date, status, total_amount)
SELECT
    floor(random() * 100 + 1)::int AS customer_id,
    CASE WHEN random() < 0.8
         THEN floor(random() * 10 + 1)::int  -- Sales employees (1-10)
         ELSE NULL
    END AS employee_id,
    (DATE '2023-01-01' + (random() * 730)::int)::date AS order_date,
    (ARRAY['pending','confirmed','shipped','delivered','delivered','delivered','cancelled'])[floor(random()*7+1)::int] AS status,
    0  -- will be updated after order_items
FROM generate_series(1, 500);

-- ============================================================
-- 6. ORDER_ITEMS (~1500 rows)
-- ============================================================
CREATE TABLE order_items (
    item_id     SERIAL PRIMARY KEY,
    order_id    INT NOT NULL REFERENCES orders(order_id),
    product_id  INT NOT NULL REFERENCES products(product_id),
    quantity    INT NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL,
    line_total  NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- Insert 1-5 items per order
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    o.order_id,
    p.product_id,
    floor(random() * 5 + 1)::int AS quantity,
    p.unit_price
FROM orders o
CROSS JOIN LATERAL (
    SELECT product_id, unit_price
    FROM products
    ORDER BY random()
    LIMIT (floor(random() * 4 + 1)::int)
) p;

-- Update order totals from line items
UPDATE orders o SET total_amount = (
    SELECT COALESCE(SUM(line_total), 0) FROM order_items WHERE order_id = o.order_id
);

-- ============================================================
-- Useful views
-- ============================================================
CREATE VIEW v_customer_orders AS
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.segment,
    c.country,
    COUNT(o.order_id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.segment, c.country;

CREATE VIEW v_monthly_sales AS
SELECT
    DATE_TRUNC('month', o.order_date)::date AS month,
    COUNT(o.order_id) AS order_count,
    SUM(o.total_amount) AS revenue,
    COUNT(DISTINCT o.customer_id) AS unique_customers
FROM orders o
WHERE o.status != 'cancelled'
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY month;

CREATE VIEW v_product_performance AS
SELECT
    p.product_name,
    p.category,
    COUNT(oi.item_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.line_total) AS total_revenue,
    SUM(oi.line_total) - SUM(oi.quantity * p.cost_price) AS total_profit
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category;
