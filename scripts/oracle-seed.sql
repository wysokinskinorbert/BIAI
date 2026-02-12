-- BIAI Test Database Seed - Oracle
-- 6 business tables with realistic data
-- Runs as APP_USER (biai) in XEPDB1

-- Switch to PDB and app user (init scripts run as SYS in CDB root)
CONNECT biai/biai123@XEPDB1

-- ============================================================
-- 1. SALES_REGIONS (~10 rows)
-- ============================================================
CREATE TABLE sales_regions (
    region_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name VARCHAR2(100) NOT NULL,
    country     VARCHAR2(100) NOT NULL,
    manager     VARCHAR2(100)
);

-- Individual inserts (INSERT ALL doesn't work with IDENTITY columns)
INSERT INTO sales_regions (region_name, country, manager) VALUES ('North America East', 'USA', 'John Mitchell');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('North America West', 'USA', 'Sarah Chen');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('Europe Central', 'Germany', 'Klaus Weber');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('Europe South', 'Spain', 'Maria Garcia');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('Europe North', 'Sweden', 'Erik Johansson');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('Asia Pacific', 'Japan', 'Takeshi Yamamoto');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('South America', 'Brazil', 'Carlos Silva');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('Middle East', 'UAE', 'Ahmed Al-Rashid');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('Africa', 'South Africa', 'Thandi Nkosi');
INSERT INTO sales_regions (region_name, country, manager) VALUES ('Oceania', 'Australia', 'James Cook');
COMMIT;

-- ============================================================
-- 2. CUSTOMERS (~100 rows)
-- ============================================================
CREATE TABLE customers (
    customer_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name    VARCHAR2(100) NOT NULL,
    last_name     VARCHAR2(100) NOT NULL,
    email         VARCHAR2(200) NOT NULL UNIQUE,
    city          VARCHAR2(100),
    country       VARCHAR2(100),
    segment       VARCHAR2(50) CHECK (segment IN ('Enterprise', 'SMB', 'Startup', 'Government')),
    region_id     NUMBER REFERENCES sales_regions(region_id),
    created_at    TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- Generate 100 customers using PL/SQL
DECLARE
    TYPE str_arr IS VARRAY(70) OF VARCHAR2(100);
    v_fnames str_arr := str_arr('James','Mary','Robert','Patricia','John','Jennifer','Michael','Linda','David','Elizabeth',
        'William','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Charles','Karen',
        'Christopher','Lisa','Daniel','Nancy','Matthew','Betty','Anthony','Margaret','Mark','Sandra',
        'Anna','Maria','Elena','Sofia','Yuki','Mei','Priya','Fatima','Olga','Ingrid',
        'Hans','Pierre','Marco','Pedro','Ali','Chen','Raj','Omar','Igor','Lars');
    v_lnames str_arr := str_arr('Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez',
        'Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin',
        'Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson',
        'Walker','Young','Allen','King','Wright','Scott','Torres','Nguyen','Hill','Flores',
        'Weber','Mueller','Schmidt','Fischer','Yamamoto','Tanaka','Kumar','Singh','Ivanov','Petrov');
    v_cities str_arr := str_arr('New York','Los Angeles','Chicago','Houston','Phoenix','San Francisco','Seattle','Denver',
        'Berlin','Munich','Madrid','Barcelona','Stockholm','Tokyo','Osaka','Sao Paulo',
        'Dubai','Johannesburg','Sydney','Melbourne','London','Paris','Rome','Toronto','Vancouver');
    v_countries str_arr := str_arr('USA','USA','USA','USA','USA','USA','USA','USA',
        'Germany','Germany','Spain','Spain','Sweden','Japan','Japan','Brazil',
        'UAE','South Africa','Australia','Australia','UK','France','Italy','Canada','Canada');

    TYPE seg_arr IS VARRAY(4) OF VARCHAR2(20);
    v_segments seg_arr := seg_arr('Enterprise','SMB','Startup','Government');

    v_fname VARCHAR2(100);
    v_lname VARCHAR2(100);
    v_email VARCHAR2(200);
    v_city VARCHAR2(100);
    v_country VARCHAR2(100);
    v_seg VARCHAR2(50);
    v_rid NUMBER;
    v_dt DATE;
BEGIN
    FOR i IN 1..100 LOOP
        v_fname := v_fnames(TRUNC(DBMS_RANDOM.VALUE(1, v_fnames.COUNT + 1)));
        v_lname := v_lnames(TRUNC(DBMS_RANDOM.VALUE(1, v_lnames.COUNT + 1)));
        v_email := 'user' || i || '_' || LOWER(DBMS_RANDOM.STRING('x', 6)) || '@example.com';
        v_city := v_cities(TRUNC(DBMS_RANDOM.VALUE(1, v_cities.COUNT + 1)));
        v_country := v_countries(TRUNC(DBMS_RANDOM.VALUE(1, v_countries.COUNT + 1)));
        v_seg := v_segments(TRUNC(DBMS_RANDOM.VALUE(1, v_segments.COUNT + 1)));
        v_rid := TRUNC(DBMS_RANDOM.VALUE(1, 11));
        v_dt := SYSDATE - TRUNC(DBMS_RANDOM.VALUE(0, 730));
        INSERT INTO customers (first_name, last_name, email, city, country, segment, region_id, created_at)
        VALUES (v_fname, v_lname, v_email, v_city, v_country, v_seg, v_rid, CAST(v_dt AS TIMESTAMP));
    END LOOP;
    COMMIT;
END;
/

-- ============================================================
-- 3. PRODUCTS (~50 rows)
-- ============================================================
CREATE TABLE products (
    product_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name VARCHAR2(200) NOT NULL,
    category     VARCHAR2(100) NOT NULL,
    unit_price   NUMBER(10,2) NOT NULL,
    cost_price   NUMBER(10,2) NOT NULL
);

-- Individual inserts for products (IDENTITY requires separate statements)
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Enterprise Analytics Suite', 'Software', 4999.99, 2499.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Cloud Data Warehouse License', 'Software', 2499.99, 1249.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('BI Dashboard Pro', 'Software', 1299.99, 519.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Data Integration Platform', 'Software', 3499.99, 1399.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('ML Model Server', 'Software', 5999.99, 2999.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Real-time Streaming Engine', 'Software', 1999.99, 799.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('API Gateway Premium', 'Software', 899.99, 359.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Security Compliance Module', 'Software', 1499.99, 599.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('DevOps Pipeline Toolkit', 'Software', 799.99, 319.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Database Optimizer Pro', 'Software', 1199.99, 479.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Rack Server RS-4000', 'Hardware', 12999.99, 7799.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Rack Server RS-2000', 'Hardware', 7999.99, 4799.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Storage Array SA-500', 'Hardware', 24999.99, 14999.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Network Switch NS-48', 'Hardware', 3499.99, 2099.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('GPU Compute Node GC-8', 'Hardware', 18999.99, 11399.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Edge Computing Device', 'Hardware', 2499.99, 1499.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('SSD Module 4TB', 'Hardware', 899.99, 539.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('RAM Module 128GB', 'Hardware', 649.99, 389.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Fiber Optic Cable Kit', 'Hardware', 299.99, 179.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('UPS Power Unit 3000VA', 'Hardware', 1899.99, 1139.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('24/7 Premium Support', 'Services', 4999.99, 2999.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Implementation Consulting', 'Services', 14999.99, 8999.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Data Migration Service', 'Services', 9999.99, 5999.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Staff Training Program', 'Services', 2999.99, 1499.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Architecture Review', 'Services', 7499.99, 4499.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Performance Tuning', 'Services', 5999.99, 3599.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Security Audit', 'Services', 8999.99, 5399.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Disaster Recovery Setup', 'Services', 11999.99, 7199.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Custom Integration', 'Services', 19999.99, 11999.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Managed Database Service', 'Services', 3499.99, 2099.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Basic Support Plan', 'Subscription', 99.99, 29.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Professional Plan', 'Subscription', 299.99, 89.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Enterprise Plan', 'Subscription', 999.99, 299.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Data Lake Storage 1TB', 'Subscription', 149.99, 44.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Data Lake Storage 10TB', 'Subscription', 999.99, 299.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('API Calls - 1M/month', 'Subscription', 49.99, 14.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('API Calls - 10M/month', 'Subscription', 399.99, 119.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Monitoring and Alerting', 'Subscription', 199.99, 59.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Log Analytics 100GB', 'Subscription', 249.99, 74.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Backup Service Premium', 'Subscription', 179.99, 53.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('IoT Sensor Pack S', 'Hardware', 499.99, 299.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('IoT Sensor Pack M', 'Hardware', 1299.99, 779.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('IoT Sensor Pack L', 'Hardware', 2999.99, 1799.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('AI Training Bootcamp', 'Services', 4499.99, 2249.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Compliance Report Generator', 'Software', 699.99, 279.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('ETL Pipeline Builder', 'Software', 1599.99, 639.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Data Quality Scanner', 'Software', 899.99, 359.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Report Designer', 'Software', 599.99, 239.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Mobile Analytics App', 'Software', 399.99, 159.99);
INSERT INTO products (product_name, category, unit_price, cost_price) VALUES ('Embedded BI SDK', 'Software', 2999.99, 1199.99);
COMMIT;

-- ============================================================
-- 4. EMPLOYEES (~30 rows)
-- ============================================================
CREATE TABLE employees (
    employee_id  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name   VARCHAR2(100) NOT NULL,
    last_name    VARCHAR2(100) NOT NULL,
    department   VARCHAR2(100) NOT NULL,
    title        VARCHAR2(100),
    hire_date    DATE NOT NULL,
    salary       NUMBER(10,2) NOT NULL,
    region_id    NUMBER REFERENCES sales_regions(region_id)
);

INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Alice', 'Morgan', 'Sales', 'VP of Sales', DATE '2019-03-15', 145000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Bob', 'Chen', 'Sales', 'Sales Director', DATE '2020-01-10', 120000.00, 2);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Carol', 'Weber', 'Sales', 'Sales Director', DATE '2019-07-22', 118000.00, 3);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('David', 'Garcia', 'Sales', 'Account Executive', DATE '2021-04-05', 85000.00, 4);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Eva', 'Johansson', 'Sales', 'Account Executive', DATE '2021-09-18', 82000.00, 5);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Frank', 'Yamamoto', 'Sales', 'Account Executive', DATE '2022-02-14', 80000.00, 6);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Grace', 'Silva', 'Sales', 'Sales Rep', DATE '2022-06-01', 65000.00, 7);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Henry', 'Al-Rashid', 'Sales', 'Sales Rep', DATE '2023-01-09', 63000.00, 8);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Irene', 'Nkosi', 'Sales', 'Sales Rep', DATE '2023-05-20', 60000.00, 9);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Jack', 'Cook', 'Sales', 'Sales Rep', DATE '2023-08-11', 62000.00, 10);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Kate', 'Thompson', 'Engineering', 'CTO', DATE '2018-11-01', 175000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Liam', 'Nguyen', 'Engineering', 'Senior Engineer', DATE '2020-03-15', 135000.00, 2);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Maya', 'Petrov', 'Engineering', 'Senior Engineer', DATE '2020-06-22', 130000.00, 3);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Noah', 'Kumar', 'Engineering', 'Engineer', DATE '2021-08-10', 105000.00, 6);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Olivia', 'Fischer', 'Engineering', 'Engineer', DATE '2022-01-15', 100000.00, 3);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Peter', 'Brown', 'Engineering', 'Junior Engineer', DATE '2023-04-01', 78000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Quinn', 'Davis', 'Marketing', 'VP of Marketing', DATE '2019-05-10', 140000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Rachel', 'Martinez', 'Marketing', 'Marketing Manager', DATE '2020-09-14', 95000.00, 4);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Sam', 'Wilson', 'Marketing', 'Content Specialist', DATE '2022-03-22', 70000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Tina', 'Lee', 'Marketing', 'Digital Marketing', DATE '2022-11-07', 72000.00, 6);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Uma', 'Patel', 'Support', 'Support Director', DATE '2019-08-19', 110000.00, 6);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Victor', 'Santos', 'Support', 'Support Engineer', DATE '2021-02-28', 75000.00, 7);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Wendy', 'Mueller', 'Support', 'Support Engineer', DATE '2021-10-15', 73000.00, 3);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Xavier', 'Torres', 'Support', 'Support Analyst', DATE '2023-02-01', 58000.00, 4);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Yara', 'Kim', 'Finance', 'CFO', DATE '2018-09-01', 165000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Zach', 'Anderson', 'Finance', 'Financial Analyst', DATE '2021-05-17', 88000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Amy', 'Robinson', 'Finance', 'Accountant', DATE '2022-07-10', 72000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Ben', 'White', 'HR', 'HR Director', DATE '2019-12-01', 115000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Chloe', 'Harris', 'HR', 'HR Specialist', DATE '2022-04-18', 68000.00, 1);
INSERT INTO employees (first_name, last_name, department, title, hire_date, salary, region_id) VALUES ('Derek', 'Clark', 'Operations', 'COO', DATE '2018-06-15', 155000.00, 1);
COMMIT;

-- ============================================================
-- 5. ORDERS (~500 rows)
-- ============================================================
CREATE TABLE orders (
    order_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id  NUMBER NOT NULL REFERENCES customers(customer_id),
    employee_id  NUMBER REFERENCES employees(employee_id),
    order_date   DATE NOT NULL,
    status       VARCHAR2(20) CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    total_amount NUMBER(12,2) DEFAULT 0
);

DECLARE
    TYPE status_arr IS VARRAY(7) OF VARCHAR2(20);
    v_statuses status_arr := status_arr('pending','confirmed','shipped','delivered','delivered','delivered','cancelled');
    v_emp_id NUMBER;
    v_status VARCHAR2(20);
    v_cust_id NUMBER;
    v_odate DATE;
BEGIN
    FOR i IN 1..500 LOOP
        IF DBMS_RANDOM.VALUE < 0.8 THEN
            v_emp_id := TRUNC(DBMS_RANDOM.VALUE(1, 11));
        ELSE
            v_emp_id := NULL;
        END IF;
        v_status := v_statuses(TRUNC(DBMS_RANDOM.VALUE(1, v_statuses.COUNT + 1)));
        v_cust_id := TRUNC(DBMS_RANDOM.VALUE(1, 101));
        v_odate := DATE '2023-01-01' + TRUNC(DBMS_RANDOM.VALUE(0, 731));
        INSERT INTO orders (customer_id, employee_id, order_date, status, total_amount)
        VALUES (v_cust_id, v_emp_id, v_odate, v_status, 0);
    END LOOP;
    COMMIT;
END;
/

-- ============================================================
-- 6. ORDER_ITEMS (~1500 rows)
-- ============================================================
CREATE TABLE order_items (
    item_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id    NUMBER NOT NULL REFERENCES orders(order_id),
    product_id  NUMBER NOT NULL REFERENCES products(product_id),
    quantity    NUMBER NOT NULL CHECK (quantity > 0),
    unit_price  NUMBER(10,2) NOT NULL,
    line_total  NUMBER(12,2) GENERATED ALWAYS AS (quantity * unit_price) VIRTUAL
);

-- Insert 1-4 items per order
DECLARE
    v_num_items NUMBER;
    v_pid NUMBER;
    v_price NUMBER(10,2);
BEGIN
    FOR rec IN (SELECT order_id FROM orders) LOOP
        v_num_items := TRUNC(DBMS_RANDOM.VALUE(1, 5));
        FOR j IN 1..v_num_items LOOP
            v_pid := TRUNC(DBMS_RANDOM.VALUE(1, 51));
            SELECT unit_price INTO v_price FROM products WHERE product_id = v_pid;
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (rec.order_id, v_pid, TRUNC(DBMS_RANDOM.VALUE(1, 6)), v_price);
        END LOOP;
    END LOOP;
    COMMIT;
END;
/

-- Update order totals from line items
UPDATE orders o SET total_amount = (
    SELECT NVL(SUM(line_total), 0) FROM order_items WHERE order_id = o.order_id
);
COMMIT;

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
    NVL(SUM(o.total_amount), 0) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.segment, c.country;

CREATE VIEW v_monthly_sales AS
SELECT
    TRUNC(o.order_date, 'MM') AS month,
    COUNT(o.order_id) AS order_count,
    SUM(o.total_amount) AS revenue,
    COUNT(DISTINCT o.customer_id) AS unique_customers
FROM orders o
WHERE o.status != 'cancelled'
GROUP BY TRUNC(o.order_date, 'MM')
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
