-- BIAI Process Discovery Test - Oracle
-- 5 dedicated schemas (business domains) with realistic tables
-- Each schema has status columns discoverable by ProcessDiscoveryEngine
-- Run after oracle-seed.sql (01), oracle-process-seed.sql (02), oracle-process-fix.sql (03)

-- ============================================================
-- PHASE 1: Create schemas (users) as SYSDBA
-- ============================================================
CONNECT sys/testpass123@XEPDB1 AS SYSDBA

-- Create 5 domain schemas
CREATE USER hr_proc IDENTIFIED BY biai123 DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS;
CREATE USER logistics_proc IDENTIFIED BY biai123 DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS;
CREATE USER finance_proc IDENTIFIED BY biai123 DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS;
CREATE USER project_proc IDENTIFIED BY biai123 DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS;
CREATE USER healthcare_proc IDENTIFIED BY biai123 DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS;

GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO hr_proc;
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO logistics_proc;
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO finance_proc;
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO project_proc;
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO healthcare_proc;


-- ============================================================
-- SCHEMA 1: HR_PROC (Human Resources) — 5 tables, ~700 rows
-- ============================================================
CONNECT hr_proc/biai123@XEPDB1

CREATE TABLE departments (
    department_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name VARCHAR2(100) NOT NULL,
    location        VARCHAR2(100),
    budget          NUMBER(12,2)
);

CREATE TABLE employees (
    employee_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name        VARCHAR2(100) NOT NULL,
    last_name         VARCHAR2(100) NOT NULL,
    email             VARCHAR2(200),
    department_id     NUMBER REFERENCES departments(department_id),
    hire_date         DATE NOT NULL,
    employment_status VARCHAR2(30) NOT NULL,
    salary            NUMBER(10,2)
);

CREATE TABLE leave_requests (
    request_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id   NUMBER REFERENCES employees(employee_id),
    leave_type    VARCHAR2(30) NOT NULL,
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    status        VARCHAR2(30) NOT NULL,
    requested_at  TIMESTAMP DEFAULT SYSTIMESTAMP,
    decided_at    TIMESTAMP
);

CREATE TABLE recruitment (
    recruitment_id  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id   NUMBER REFERENCES departments(department_id),
    position_title  VARCHAR2(200) NOT NULL,
    status          VARCHAR2(30) NOT NULL,
    opened_at       DATE NOT NULL,
    closed_at       DATE,
    salary_range    VARCHAR2(50)
);

CREATE TABLE candidates (
    candidate_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recruitment_id  NUMBER REFERENCES recruitment(recruitment_id),
    full_name       VARCHAR2(200) NOT NULL,
    email           VARCHAR2(200),
    stage           VARCHAR2(30) NOT NULL,
    applied_at      DATE NOT NULL,
    updated_at      TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- Seed HR_PROC data
DECLARE
    TYPE str_arr IS VARRAY(10) OF VARCHAR2(100);
    TYPE status_arr IS VARRAY(10) OF VARCHAR2(30);

    v_dept_names str_arr := str_arr('Engineering','Marketing','Sales','Finance','HR','Operations','Legal','Support');
    v_locations str_arr := str_arr('New York','San Francisco','London','Berlin','Tokyo','Sydney','Toronto','Warsaw');
    v_first_names str_arr := str_arr('James','Emma','Oliver','Sophia','William','Isabella','Benjamin','Mia','Lucas','Charlotte');
    v_last_names str_arr := str_arr('Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez');

    v_emp_statuses status_arr := status_arr('active','active','active','active','active','active','on_leave','terminated','probation','active');
    v_leave_statuses status_arr := status_arr('pending','approved','approved','approved','rejected','cancelled','approved','approved','pending','approved');
    v_leave_types str_arr := str_arr('annual','sick','annual','personal','annual','sick','maternity','annual','annual','sick');
    v_recruit_statuses status_arr := status_arr('open','screening','interviewing','offer','filled','filled','cancelled','filled','screening','open');
    v_cand_stages status_arr := status_arr('applied','phone_screen','technical_test','interview','offer_made','hired','rejected','applied','phone_screen','hired');

    v_dept_id NUMBER;
    v_emp_id NUMBER;
    v_rec_id NUMBER;
BEGIN
    -- Departments (8)
    FOR i IN 1..v_dept_names.COUNT LOOP
        INSERT INTO departments (department_name, location, budget)
        VALUES (v_dept_names(i), v_locations(i), ROUND(DBMS_RANDOM.VALUE(500000, 5000000), 2));
    END LOOP;

    -- Employees (150)
    FOR i IN 1..150 LOOP
        v_dept_id := FLOOR(DBMS_RANDOM.VALUE(1, 9));
        INSERT INTO employees (first_name, last_name, email, department_id, hire_date, employment_status, salary)
        VALUES (
            v_first_names(MOD(i, 10) + 1),
            v_last_names(MOD(i + 3, 10) + 1),
            'emp' || i || '@company.com',
            v_dept_id,
            SYSDATE - DBMS_RANDOM.VALUE(30, 3650),
            v_emp_statuses(MOD(i, 10) + 1),
            ROUND(DBMS_RANDOM.VALUE(35000, 150000), 2)
        );
    END LOOP;

    -- Leave Requests (200)
    FOR i IN 1..200 LOOP
        v_emp_id := FLOOR(DBMS_RANDOM.VALUE(1, 151));
        INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, status, requested_at, decided_at)
        VALUES (
            v_emp_id,
            v_leave_types(MOD(i, 10) + 1),
            SYSDATE + DBMS_RANDOM.VALUE(1, 90),
            SYSDATE + DBMS_RANDOM.VALUE(91, 100),
            v_leave_statuses(MOD(i, 10) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 180),
            CASE WHEN MOD(i, 10) + 1 NOT IN (1, 9)
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 30)
                 ELSE NULL END
        );
    END LOOP;

    -- Recruitment (30)
    FOR i IN 1..30 LOOP
        v_dept_id := FLOOR(DBMS_RANDOM.VALUE(1, 9));
        INSERT INTO recruitment (department_id, position_title, status, opened_at, closed_at, salary_range)
        VALUES (
            v_dept_id,
            CASE MOD(i, 5) WHEN 0 THEN 'Software Engineer' WHEN 1 THEN 'Product Manager'
                 WHEN 2 THEN 'Data Analyst' WHEN 3 THEN 'UX Designer' ELSE 'DevOps Engineer' END,
            v_recruit_statuses(MOD(i, 10) + 1),
            SYSDATE - DBMS_RANDOM.VALUE(30, 365),
            CASE WHEN v_recruit_statuses(MOD(i, 10) + 1) IN ('filled','cancelled')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(1, 29) ELSE NULL END,
            CASE MOD(i, 3) WHEN 0 THEN '50k-80k' WHEN 1 THEN '80k-120k' ELSE '120k-180k' END
        );
    END LOOP;

    -- Candidates (300)
    FOR i IN 1..300 LOOP
        v_rec_id := FLOOR(DBMS_RANDOM.VALUE(1, 31));
        INSERT INTO candidates (recruitment_id, full_name, email, stage, applied_at)
        VALUES (
            v_rec_id,
            v_first_names(MOD(i, 10) + 1) || ' ' || v_last_names(MOD(i + 5, 10) + 1),
            'candidate' || i || '@email.com',
            v_cand_stages(MOD(i, 10) + 1),
            SYSDATE - DBMS_RANDOM.VALUE(1, 180)
        );
    END LOOP;

    COMMIT;
END;
/


-- ============================================================
-- SCHEMA 2: LOGISTICS_PROC (Supply Chain) — 5 tables, ~1200 rows
-- ============================================================
CONNECT logistics_proc/biai123@XEPDB1

CREATE TABLE warehouses (
    warehouse_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warehouse_name VARCHAR2(100) NOT NULL,
    city           VARCHAR2(100),
    capacity       NUMBER
);

CREATE TABLE suppliers (
    supplier_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_name VARCHAR2(200) NOT NULL,
    country       VARCHAR2(100),
    contact_email VARCHAR2(200),
    status        VARCHAR2(30) NOT NULL
);

CREATE TABLE purchase_orders (
    po_id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_id    NUMBER REFERENCES suppliers(supplier_id),
    warehouse_id   NUMBER REFERENCES warehouses(warehouse_id),
    order_date     DATE NOT NULL,
    total_amount   NUMBER(12,2),
    status         VARCHAR2(30) NOT NULL,
    expected_date  DATE,
    received_date  DATE
);

CREATE TABLE shipments (
    shipment_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    po_id          NUMBER REFERENCES purchase_orders(po_id),
    carrier        VARCHAR2(100),
    tracking_no    VARCHAR2(100),
    status         VARCHAR2(30) NOT NULL,
    shipped_at     TIMESTAMP,
    delivered_at   TIMESTAMP
);

CREATE TABLE quality_checks (
    check_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    po_id          NUMBER REFERENCES purchase_orders(po_id),
    inspector      VARCHAR2(100),
    check_date     DATE NOT NULL,
    status         VARCHAR2(30) NOT NULL,
    defect_count   NUMBER DEFAULT 0,
    notes          VARCHAR2(500)
);

-- Seed LOGISTICS_PROC data
DECLARE
    TYPE str_arr IS VARRAY(10) OF VARCHAR2(100);
    TYPE status_arr IS VARRAY(10) OF VARCHAR2(30);

    v_wh_names str_arr := str_arr('Main Warehouse','East Hub','West Distribution','Central Storage','South Depot');
    v_cities str_arr := str_arr('Chicago','Newark','Los Angeles','Dallas','Miami');
    v_supplier_names str_arr := str_arr('Global Parts Inc','Pacific Supply Co','Euro Materials Ltd','Asia Components','South Trading','Nordic Freight','Tech Parts GmbH','Rapid Logistics','Prime Materials','Atlas Supply');
    v_countries str_arr := str_arr('USA','China','Germany','Japan','Brazil','Sweden','Germany','UK','Canada','Mexico');
    v_carriers str_arr := str_arr('FedEx','DHL','UPS','Maersk','TNT','DB Schenker','Kuehne+Nagel','CEVA','XPO','DPD');

    v_supplier_statuses status_arr := status_arr('active','active','active','active','active','active','active','inactive','blacklisted','active');
    v_po_statuses status_arr := status_arr('draft','submitted','confirmed','shipped','received','inspected','stored','cancelled','confirmed','received');
    v_ship_statuses status_arr := status_arr('preparing','picked_up','in_transit','in_transit','in_transit','customs','delivered','delivered','delivered','damaged');
    v_qc_statuses status_arr := status_arr('pending','in_progress','passed','passed','passed','passed','failed','needs_recheck','passed','passed');

    v_sup_id NUMBER;
    v_wh_id NUMBER;
    v_po_id NUMBER;
BEGIN
    -- Warehouses (5)
    FOR i IN 1..v_wh_names.COUNT LOOP
        INSERT INTO warehouses (warehouse_name, city, capacity)
        VALUES (v_wh_names(i), v_cities(i), FLOOR(DBMS_RANDOM.VALUE(5000, 50000)));
    END LOOP;

    -- Suppliers (20)
    FOR i IN 1..20 LOOP
        INSERT INTO suppliers (supplier_name, country, contact_email, status)
        VALUES (
            v_supplier_names(MOD(i, 10) + 1) || CASE WHEN i > 10 THEN ' ' || i ELSE '' END,
            v_countries(MOD(i, 10) + 1),
            'supplier' || i || '@supply.com',
            v_supplier_statuses(MOD(i, 10) + 1)
        );
    END LOOP;

    -- Purchase Orders (400)
    FOR i IN 1..400 LOOP
        v_sup_id := FLOOR(DBMS_RANDOM.VALUE(1, 21));
        v_wh_id := FLOOR(DBMS_RANDOM.VALUE(1, 6));
        INSERT INTO purchase_orders (supplier_id, warehouse_id, order_date, total_amount, status, expected_date, received_date)
        VALUES (
            v_sup_id, v_wh_id,
            SYSDATE - DBMS_RANDOM.VALUE(1, 365),
            ROUND(DBMS_RANDOM.VALUE(1000, 500000), 2),
            v_po_statuses(MOD(i, 10) + 1),
            SYSDATE + DBMS_RANDOM.VALUE(1, 60),
            CASE WHEN v_po_statuses(MOD(i, 10) + 1) IN ('received','inspected','stored')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(1, 30) ELSE NULL END
        );
    END LOOP;

    -- Shipments (350)
    FOR i IN 1..350 LOOP
        v_po_id := FLOOR(DBMS_RANDOM.VALUE(1, 401));
        INSERT INTO shipments (po_id, carrier, tracking_no, status, shipped_at, delivered_at)
        VALUES (
            v_po_id,
            v_carriers(MOD(i, 10) + 1),
            'TRK' || LPAD(i, 8, '0'),
            v_ship_statuses(MOD(i, 10) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 60),
            CASE WHEN v_ship_statuses(MOD(i, 10) + 1) IN ('delivered','damaged')
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 10) ELSE NULL END
        );
    END LOOP;

    -- Quality Checks (400)
    FOR i IN 1..400 LOOP
        v_po_id := FLOOR(DBMS_RANDOM.VALUE(1, 401));
        INSERT INTO quality_checks (po_id, inspector, check_date, status, defect_count, notes)
        VALUES (
            v_po_id,
            'Inspector ' || MOD(i, 8) + 1,
            SYSDATE - DBMS_RANDOM.VALUE(1, 90),
            v_qc_statuses(MOD(i, 10) + 1),
            CASE WHEN v_qc_statuses(MOD(i, 10) + 1) = 'failed' THEN FLOOR(DBMS_RANDOM.VALUE(1, 20)) ELSE 0 END,
            CASE WHEN v_qc_statuses(MOD(i, 10) + 1) = 'failed' THEN 'Defects found in batch' ELSE NULL END
        );
    END LOOP;

    COMMIT;
END;
/


-- ============================================================
-- SCHEMA 3: FINANCE_PROC (Financial) — 5 tables, ~1200 rows
-- ============================================================
CONNECT finance_proc/biai123@XEPDB1

CREATE TABLE invoices (
    invoice_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_no    VARCHAR2(50) NOT NULL,
    client_name   VARCHAR2(200),
    amount        NUMBER(12,2) NOT NULL,
    currency      VARCHAR2(3) DEFAULT 'USD',
    status        VARCHAR2(30) NOT NULL,
    issued_date   DATE NOT NULL,
    due_date      DATE NOT NULL,
    paid_date     DATE
);

CREATE TABLE payments (
    payment_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id    NUMBER REFERENCES invoices(invoice_id),
    amount        NUMBER(12,2) NOT NULL,
    payment_method VARCHAR2(30),
    status        VARCHAR2(30) NOT NULL,
    initiated_at  TIMESTAMP NOT NULL,
    completed_at  TIMESTAMP
);

CREATE TABLE expense_claims (
    claim_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_name VARCHAR2(200) NOT NULL,
    department    VARCHAR2(100),
    amount        NUMBER(10,2) NOT NULL,
    category      VARCHAR2(50),
    status        VARCHAR2(30) NOT NULL,
    submitted_at  TIMESTAMP NOT NULL,
    decided_at    TIMESTAMP
);

CREATE TABLE budgets (
    budget_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department    VARCHAR2(100) NOT NULL,
    fiscal_year   NUMBER(4) NOT NULL,
    amount        NUMBER(14,2) NOT NULL,
    status        VARCHAR2(30) NOT NULL,
    created_at    DATE NOT NULL,
    approved_at   DATE
);

CREATE TABLE audit_items (
    audit_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    audit_area    VARCHAR2(200) NOT NULL,
    auditor       VARCHAR2(100),
    status        VARCHAR2(30) NOT NULL,
    priority      VARCHAR2(10),
    planned_date  DATE NOT NULL,
    completed_date DATE,
    findings      VARCHAR2(1000)
);

-- Seed FINANCE_PROC data
DECLARE
    TYPE str_arr IS VARRAY(10) OF VARCHAR2(100);
    TYPE status_arr IS VARRAY(10) OF VARCHAR2(30);

    v_clients str_arr := str_arr('Acme Corp','Beta Industries','Gamma Tech','Delta Services','Epsilon Ltd','Zeta Group','Eta Systems','Theta Inc','Iota Solutions','Kappa Trading');
    v_depts str_arr := str_arr('Engineering','Marketing','Sales','Finance','HR','Operations','Legal','Support');
    v_categories str_arr := str_arr('travel','meals','office_supplies','software','training','conference','equipment','transport');
    v_audit_areas str_arr := str_arr('Revenue Recognition','Payroll Compliance','Vendor Payments','Tax Filing','Inventory Valuation','IT Security','Data Privacy','Financial Controls');
    v_methods str_arr := str_arr('wire_transfer','credit_card','ach','check','wire_transfer','credit_card','ach','credit_card');

    v_inv_statuses status_arr := status_arr('draft','sent','sent','viewed','partial_payment','paid','paid','paid','overdue','written_off');
    v_pay_statuses status_arr := status_arr('initiated','processing','completed','completed','completed','completed','failed','reversed','completed','completed');
    v_exp_statuses status_arr := status_arr('submitted','under_review','approved','approved','approved','rejected','reimbursed','reimbursed','reimbursed','submitted');
    v_bud_statuses status_arr := status_arr('draft','proposed','approved','active','active','active','frozen','closed','active','approved');
    v_aud_statuses status_arr := status_arr('planned','in_progress','findings_reported','remediation','verified','closed','closed','closed','in_progress','planned');

    v_inv_id NUMBER;
BEGIN
    -- Invoices (400)
    FOR i IN 1..400 LOOP
        INSERT INTO invoices (invoice_no, client_name, amount, currency, status, issued_date, due_date, paid_date)
        VALUES (
            'INV-' || LPAD(i, 6, '0'),
            v_clients(MOD(i, 10) + 1),
            ROUND(DBMS_RANDOM.VALUE(500, 100000), 2),
            CASE MOD(i, 4) WHEN 0 THEN 'EUR' WHEN 1 THEN 'GBP' ELSE 'USD' END,
            v_inv_statuses(MOD(i, 10) + 1),
            SYSDATE - DBMS_RANDOM.VALUE(30, 365),
            SYSDATE - DBMS_RANDOM.VALUE(0, 30),
            CASE WHEN v_inv_statuses(MOD(i, 10) + 1) IN ('paid','partial_payment')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(0, 15) ELSE NULL END
        );
    END LOOP;

    -- Payments (350)
    FOR i IN 1..350 LOOP
        v_inv_id := FLOOR(DBMS_RANDOM.VALUE(1, 401));
        INSERT INTO payments (invoice_id, amount, payment_method, status, initiated_at, completed_at)
        VALUES (
            v_inv_id,
            ROUND(DBMS_RANDOM.VALUE(100, 50000), 2),
            v_methods(MOD(i, 8) + 1),
            v_pay_statuses(MOD(i, 10) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 180),
            CASE WHEN v_pay_statuses(MOD(i, 10) + 1) IN ('completed','reversed')
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 7) ELSE NULL END
        );
    END LOOP;

    -- Expense Claims (200)
    FOR i IN 1..200 LOOP
        INSERT INTO expense_claims (employee_name, department, amount, category, status, submitted_at, decided_at)
        VALUES (
            'Employee ' || i,
            v_depts(MOD(i, 8) + 1),
            ROUND(DBMS_RANDOM.VALUE(25, 5000), 2),
            v_categories(MOD(i, 8) + 1),
            v_exp_statuses(MOD(i, 10) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 120),
            CASE WHEN v_exp_statuses(MOD(i, 10) + 1) NOT IN ('submitted')
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 14) ELSE NULL END
        );
    END LOOP;

    -- Budgets (30)
    FOR i IN 1..30 LOOP
        INSERT INTO budgets (department, fiscal_year, amount, status, created_at, approved_at)
        VALUES (
            v_depts(MOD(i, 8) + 1),
            2024 + MOD(i, 3),
            ROUND(DBMS_RANDOM.VALUE(100000, 5000000), 2),
            v_bud_statuses(MOD(i, 10) + 1),
            SYSDATE - DBMS_RANDOM.VALUE(30, 365),
            CASE WHEN v_bud_statuses(MOD(i, 10) + 1) NOT IN ('draft','proposed')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(1, 29) ELSE NULL END
        );
    END LOOP;

    -- Audit Items (200)
    FOR i IN 1..200 LOOP
        INSERT INTO audit_items (audit_area, auditor, status, priority, planned_date, completed_date, findings)
        VALUES (
            v_audit_areas(MOD(i, 8) + 1),
            'Auditor ' || MOD(i, 5) + 1,
            v_aud_statuses(MOD(i, 10) + 1),
            CASE MOD(i, 3) WHEN 0 THEN 'high' WHEN 1 THEN 'medium' ELSE 'low' END,
            SYSDATE - DBMS_RANDOM.VALUE(1, 180),
            CASE WHEN v_aud_statuses(MOD(i, 10) + 1) IN ('verified','closed')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(0, 30) ELSE NULL END,
            CASE WHEN v_aud_statuses(MOD(i, 10) + 1) IN ('findings_reported','remediation','verified','closed')
                 THEN 'Findings documented and action plan created' ELSE NULL END
        );
    END LOOP;

    COMMIT;
END;
/


-- ============================================================
-- SCHEMA 4: PROJECT_PROC (Project Management) — 5 tables, ~1400 rows
-- ============================================================
CONNECT project_proc/biai123@XEPDB1

CREATE TABLE projects (
    project_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name  VARCHAR2(200) NOT NULL,
    project_code  VARCHAR2(20),
    sponsor       VARCHAR2(100),
    status        VARCHAR2(30) NOT NULL,
    start_date    DATE NOT NULL,
    end_date      DATE,
    budget        NUMBER(12,2)
);

CREATE TABLE milestones (
    milestone_id  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id    NUMBER REFERENCES projects(project_id),
    milestone_name VARCHAR2(200) NOT NULL,
    status        VARCHAR2(30) NOT NULL,
    due_date      DATE NOT NULL,
    completed_date DATE
);

CREATE TABLE tasks (
    task_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    milestone_id  NUMBER REFERENCES milestones(milestone_id),
    task_name     VARCHAR2(200) NOT NULL,
    assignee      VARCHAR2(100),
    status        VARCHAR2(30) NOT NULL,
    priority      VARCHAR2(10),
    created_at    TIMESTAMP DEFAULT SYSTIMESTAMP,
    completed_at  TIMESTAMP,
    estimated_hours NUMBER(5,1)
);

CREATE TABLE change_requests (
    cr_id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id    NUMBER REFERENCES projects(project_id),
    title         VARCHAR2(200) NOT NULL,
    description   VARCHAR2(1000),
    status        VARCHAR2(30) NOT NULL,
    impact        VARCHAR2(10),
    submitted_at  TIMESTAMP NOT NULL,
    decided_at    TIMESTAMP
);

CREATE TABLE risk_register (
    risk_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id    NUMBER REFERENCES projects(project_id),
    risk_title    VARCHAR2(200) NOT NULL,
    category      VARCHAR2(50),
    probability   VARCHAR2(10),
    impact_level  VARCHAR2(10),
    status        VARCHAR2(30) NOT NULL,
    identified_at DATE NOT NULL,
    mitigated_at  DATE
);

-- Seed PROJECT_PROC data
DECLARE
    TYPE str_arr IS VARRAY(10) OF VARCHAR2(100);
    TYPE status_arr IS VARRAY(10) OF VARCHAR2(30);

    v_proj_names str_arr := str_arr('Cloud Migration','ERP Upgrade','Mobile App v2','Data Lake','Security Audit','CRM Integration','API Gateway','Microservices','DevOps Pipeline','AI Platform');
    v_sponsors str_arr := str_arr('CTO Office','VP Engineering','Product Team','Data Team','Security Team','Sales VP','Platform Team','Architecture','DevOps Lead','AI Lead');
    v_assignees str_arr := str_arr('Alice','Bob','Charlie','Diana','Eve','Frank','Grace','Henry','Iris','Jack');
    v_risk_cats str_arr := str_arr('technical','schedule','budget','resource','quality','scope','compliance','vendor');

    v_proj_statuses status_arr := status_arr('planning','approved','in_progress','in_progress','in_progress','in_progress','on_hold','completed','completed','cancelled');
    v_mile_statuses status_arr := status_arr('planned','in_progress','in_progress','completed','completed','completed','delayed','cancelled','completed','planned');
    v_task_statuses status_arr := status_arr('backlog','todo','in_progress','in_progress','review','testing','done','done','done','blocked');
    v_cr_statuses status_arr := status_arr('submitted','assessment','approved','approved','rejected','implemented','implemented','submitted','approved','assessment');
    v_risk_statuses status_arr := status_arr('identified','assessed','mitigated','mitigated','accepted','closed','closed','closed','identified','assessed');

    v_proj_id NUMBER;
    v_mile_id NUMBER;
BEGIN
    -- Projects (50)
    FOR i IN 1..50 LOOP
        INSERT INTO projects (project_name, project_code, sponsor, status, start_date, end_date, budget)
        VALUES (
            v_proj_names(MOD(i, 10) + 1) || CASE WHEN i > 10 THEN ' Phase ' || CEIL(i/10) ELSE '' END,
            'PRJ-' || LPAD(i, 4, '0'),
            v_sponsors(MOD(i, 10) + 1),
            v_proj_statuses(MOD(i, 10) + 1),
            SYSDATE - DBMS_RANDOM.VALUE(30, 730),
            CASE WHEN v_proj_statuses(MOD(i, 10) + 1) IN ('completed','cancelled')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(1, 30) ELSE SYSDATE + DBMS_RANDOM.VALUE(30, 365) END,
            ROUND(DBMS_RANDOM.VALUE(50000, 2000000), 2)
        );
    END LOOP;

    -- Milestones (200)
    FOR i IN 1..200 LOOP
        v_proj_id := FLOOR(DBMS_RANDOM.VALUE(1, 51));
        INSERT INTO milestones (project_id, milestone_name, status, due_date, completed_date)
        VALUES (
            v_proj_id,
            CASE MOD(i, 5) WHEN 0 THEN 'Requirements' WHEN 1 THEN 'Design' WHEN 2 THEN 'Development'
                 WHEN 3 THEN 'Testing' ELSE 'Deployment' END || ' - M' || i,
            v_mile_statuses(MOD(i, 10) + 1),
            SYSDATE + DBMS_RANDOM.VALUE(-60, 180),
            CASE WHEN v_mile_statuses(MOD(i, 10) + 1) = 'completed'
                 THEN SYSDATE - DBMS_RANDOM.VALUE(1, 60) ELSE NULL END
        );
    END LOOP;

    -- Tasks (800)
    FOR i IN 1..800 LOOP
        v_mile_id := FLOOR(DBMS_RANDOM.VALUE(1, 201));
        INSERT INTO tasks (milestone_id, task_name, assignee, status, priority, completed_at, estimated_hours)
        VALUES (
            v_mile_id,
            'Task ' || i || ': ' || CASE MOD(i, 6) WHEN 0 THEN 'Implement feature' WHEN 1 THEN 'Write tests'
                 WHEN 2 THEN 'Code review' WHEN 3 THEN 'Documentation' WHEN 4 THEN 'Bug fix' ELSE 'Research' END,
            v_assignees(MOD(i, 10) + 1),
            v_task_statuses(MOD(i, 10) + 1),
            CASE MOD(i, 4) WHEN 0 THEN 'high' WHEN 1 THEN 'medium' WHEN 2 THEN 'low' ELSE 'critical' END,
            CASE WHEN v_task_statuses(MOD(i, 10) + 1) = 'done'
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 90) ELSE NULL END,
            ROUND(DBMS_RANDOM.VALUE(1, 40), 1)
        );
    END LOOP;

    -- Change Requests (150)
    FOR i IN 1..150 LOOP
        v_proj_id := FLOOR(DBMS_RANDOM.VALUE(1, 51));
        INSERT INTO change_requests (project_id, title, description, status, impact, submitted_at, decided_at)
        VALUES (
            v_proj_id,
            'CR-' || i || ': ' || CASE MOD(i, 4) WHEN 0 THEN 'Scope expansion' WHEN 1 THEN 'Timeline adjustment'
                 WHEN 2 THEN 'Resource reallocation' ELSE 'Technology change' END,
            'Change request description for item ' || i,
            v_cr_statuses(MOD(i, 10) + 1),
            CASE MOD(i, 3) WHEN 0 THEN 'high' WHEN 1 THEN 'medium' ELSE 'low' END,
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 180),
            CASE WHEN v_cr_statuses(MOD(i, 10) + 1) NOT IN ('submitted','assessment')
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 30) ELSE NULL END
        );
    END LOOP;

    -- Risk Register (200)
    FOR i IN 1..200 LOOP
        v_proj_id := FLOOR(DBMS_RANDOM.VALUE(1, 51));
        INSERT INTO risk_register (project_id, risk_title, category, probability, impact_level, status, identified_at, mitigated_at)
        VALUES (
            v_proj_id,
            'Risk ' || i || ': ' || CASE MOD(i, 5) WHEN 0 THEN 'Resource shortage' WHEN 1 THEN 'Technical debt'
                 WHEN 2 THEN 'Vendor dependency' WHEN 3 THEN 'Scope creep' ELSE 'Integration failure' END,
            v_risk_cats(MOD(i, 8) + 1),
            CASE MOD(i, 3) WHEN 0 THEN 'high' WHEN 1 THEN 'medium' ELSE 'low' END,
            CASE MOD(i, 3) WHEN 0 THEN 'critical' WHEN 1 THEN 'high' ELSE 'medium' END,
            v_risk_statuses(MOD(i, 10) + 1),
            SYSDATE - DBMS_RANDOM.VALUE(30, 365),
            CASE WHEN v_risk_statuses(MOD(i, 10) + 1) IN ('mitigated','closed')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(1, 30) ELSE NULL END
        );
    END LOOP;

    COMMIT;
END;
/


-- ============================================================
-- SCHEMA 5: HEALTHCARE_PROC (Clinical) — 5 tables, ~1500 rows
-- ============================================================
CONNECT healthcare_proc/biai123@XEPDB1

CREATE TABLE patients (
    patient_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name    VARCHAR2(100) NOT NULL,
    last_name     VARCHAR2(100) NOT NULL,
    date_of_birth DATE,
    gender        VARCHAR2(10),
    status        VARCHAR2(30) NOT NULL,
    registered_at TIMESTAMP NOT NULL,
    discharged_at TIMESTAMP
);

CREATE TABLE appointments (
    appointment_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    patient_id     NUMBER REFERENCES patients(patient_id),
    doctor_name    VARCHAR2(100) NOT NULL,
    department     VARCHAR2(100),
    appointment_date DATE NOT NULL,
    status         VARCHAR2(30) NOT NULL,
    scheduled_at   TIMESTAMP NOT NULL,
    completed_at   TIMESTAMP
);

CREATE TABLE treatments (
    treatment_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    patient_id     NUMBER REFERENCES patients(patient_id),
    treatment_name VARCHAR2(200) NOT NULL,
    doctor_name    VARCHAR2(100),
    status         VARCHAR2(30) NOT NULL,
    started_at     DATE NOT NULL,
    completed_at   DATE
);

CREATE TABLE lab_orders (
    lab_order_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    patient_id     NUMBER REFERENCES patients(patient_id),
    test_name      VARCHAR2(200) NOT NULL,
    ordered_by     VARCHAR2(100),
    status         VARCHAR2(30) NOT NULL,
    ordered_at     TIMESTAMP NOT NULL,
    results_at     TIMESTAMP
);

CREATE TABLE prescriptions (
    prescription_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    patient_id      NUMBER REFERENCES patients(patient_id),
    medication      VARCHAR2(200) NOT NULL,
    dosage          VARCHAR2(100),
    prescribed_by   VARCHAR2(100),
    status          VARCHAR2(30) NOT NULL,
    prescribed_at   TIMESTAMP NOT NULL,
    dispensed_at    TIMESTAMP
);

-- Seed HEALTHCARE_PROC data
DECLARE
    TYPE str_arr IS VARRAY(10) OF VARCHAR2(100);
    TYPE status_arr IS VARRAY(10) OF VARCHAR2(30);

    v_first_names str_arr := str_arr('Maria','John','Anna','Robert','Elena','Michael','Sarah','David','Laura','Thomas');
    v_last_names str_arr := str_arr('Kowalski','Mueller','Rossi','Dubois','Nielsen','Fernandez','Yamada','Singh','OBrien','Kim');
    v_doctors str_arr := str_arr('Dr. Smith','Dr. Chen','Dr. Patel','Dr. Garcia','Dr. Kim','Dr. Brown','Dr. Wilson','Dr. Taylor');
    v_departments str_arr := str_arr('Cardiology','Orthopedics','Neurology','Oncology','Pediatrics','Emergency','Internal Medicine','Surgery');
    v_treatments str_arr := str_arr('Chemotherapy','Physical Therapy','Surgery','Medication Therapy','Radiation','Dialysis','Immunotherapy','Rehabilitation');
    v_tests str_arr := str_arr('Blood Panel','MRI Scan','CT Scan','X-Ray','Urinalysis','ECG','Ultrasound','Biopsy');
    v_meds str_arr := str_arr('Amoxicillin','Ibuprofen','Metformin','Lisinopril','Atorvastatin','Omeprazole','Levothyroxine','Amlodipine');

    v_pat_statuses status_arr := status_arr('registered','active','active','active','active','active','active','discharged','discharged','deceased');
    v_apt_statuses status_arr := status_arr('scheduled','confirmed','checked_in','in_progress','completed','completed','completed','cancelled','no_show','completed');
    v_treat_statuses status_arr := status_arr('prescribed','in_progress','in_progress','in_progress','completed','completed','completed','discontinued');
    v_lab_statuses status_arr := status_arr('ordered','sample_collected','processing','processing','results_ready','results_ready','reviewed','communicated');
    v_rx_statuses status_arr := status_arr('prescribed','dispensed','active','active','active','completed','completed','cancelled');

    v_pat_id NUMBER;
BEGIN
    -- Patients (200)
    FOR i IN 1..200 LOOP
        INSERT INTO patients (first_name, last_name, date_of_birth, gender, status, registered_at, discharged_at)
        VALUES (
            v_first_names(MOD(i, 10) + 1),
            v_last_names(MOD(i + 3, 10) + 1),
            SYSDATE - DBMS_RANDOM.VALUE(7300, 36500),
            CASE MOD(i, 2) WHEN 0 THEN 'male' ELSE 'female' END,
            v_pat_statuses(MOD(i, 10) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 1095),
            CASE WHEN v_pat_statuses(MOD(i, 10) + 1) = 'discharged'
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 30) ELSE NULL END
        );
    END LOOP;

    -- Appointments (500)
    FOR i IN 1..500 LOOP
        v_pat_id := FLOOR(DBMS_RANDOM.VALUE(1, 201));
        INSERT INTO appointments (patient_id, doctor_name, department, appointment_date, status, scheduled_at, completed_at)
        VALUES (
            v_pat_id,
            v_doctors(MOD(i, 8) + 1),
            v_departments(MOD(i, 8) + 1),
            SYSDATE + DBMS_RANDOM.VALUE(-180, 60),
            v_apt_statuses(MOD(i, 10) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 365),
            CASE WHEN v_apt_statuses(MOD(i, 10) + 1) = 'completed'
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 180) ELSE NULL END
        );
    END LOOP;

    -- Treatments (300)
    FOR i IN 1..300 LOOP
        v_pat_id := FLOOR(DBMS_RANDOM.VALUE(1, 201));
        INSERT INTO treatments (patient_id, treatment_name, doctor_name, status, started_at, completed_at)
        VALUES (
            v_pat_id,
            v_treatments(MOD(i, 8) + 1),
            v_doctors(MOD(i, 8) + 1),
            v_treat_statuses(LEAST(MOD(i, 8) + 1, 8)),
            SYSDATE - DBMS_RANDOM.VALUE(1, 365),
            CASE WHEN v_treat_statuses(LEAST(MOD(i, 8) + 1, 8)) IN ('completed','discontinued')
                 THEN SYSDATE - DBMS_RANDOM.VALUE(0, 30) ELSE NULL END
        );
    END LOOP;

    -- Lab Orders (300)
    FOR i IN 1..300 LOOP
        v_pat_id := FLOOR(DBMS_RANDOM.VALUE(1, 201));
        INSERT INTO lab_orders (patient_id, test_name, ordered_by, status, ordered_at, results_at)
        VALUES (
            v_pat_id,
            v_tests(MOD(i, 8) + 1),
            v_doctors(MOD(i, 8) + 1),
            v_lab_statuses(MOD(i, 8) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 180),
            CASE WHEN v_lab_statuses(MOD(i, 8) + 1) IN ('results_ready','reviewed','communicated')
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 14) ELSE NULL END
        );
    END LOOP;

    -- Prescriptions (200)
    FOR i IN 1..200 LOOP
        v_pat_id := FLOOR(DBMS_RANDOM.VALUE(1, 201));
        INSERT INTO prescriptions (patient_id, medication, dosage, prescribed_by, status, prescribed_at, dispensed_at)
        VALUES (
            v_pat_id,
            v_meds(MOD(i, 8) + 1),
            CASE MOD(i, 3) WHEN 0 THEN '500mg 2x daily' WHEN 1 THEN '250mg 3x daily' ELSE '100mg once daily' END,
            v_doctors(MOD(i, 8) + 1),
            v_rx_statuses(MOD(i, 8) + 1),
            SYSTIMESTAMP - DBMS_RANDOM.VALUE(1, 365),
            CASE WHEN v_rx_statuses(MOD(i, 8) + 1) != 'prescribed'
                 THEN SYSTIMESTAMP - DBMS_RANDOM.VALUE(0, 14) ELSE NULL END
        );
    END LOOP;

    COMMIT;
END;
/


-- ============================================================
-- PHASE 2: Grant SELECT access to BIAI user
-- ============================================================
CONNECT sys/testpass123@XEPDB1 AS SYSDBA

-- HR_PROC grants
GRANT SELECT ON hr_proc.departments TO biai;
GRANT SELECT ON hr_proc.employees TO biai;
GRANT SELECT ON hr_proc.leave_requests TO biai;
GRANT SELECT ON hr_proc.recruitment TO biai;
GRANT SELECT ON hr_proc.candidates TO biai;

-- LOGISTICS_PROC grants
GRANT SELECT ON logistics_proc.warehouses TO biai;
GRANT SELECT ON logistics_proc.suppliers TO biai;
GRANT SELECT ON logistics_proc.purchase_orders TO biai;
GRANT SELECT ON logistics_proc.shipments TO biai;
GRANT SELECT ON logistics_proc.quality_checks TO biai;

-- FINANCE_PROC grants
GRANT SELECT ON finance_proc.invoices TO biai;
GRANT SELECT ON finance_proc.payments TO biai;
GRANT SELECT ON finance_proc.expense_claims TO biai;
GRANT SELECT ON finance_proc.budgets TO biai;
GRANT SELECT ON finance_proc.audit_items TO biai;

-- PROJECT_PROC grants
GRANT SELECT ON project_proc.projects TO biai;
GRANT SELECT ON project_proc.milestones TO biai;
GRANT SELECT ON project_proc.tasks TO biai;
GRANT SELECT ON project_proc.change_requests TO biai;
GRANT SELECT ON project_proc.risk_register TO biai;

-- HEALTHCARE_PROC grants
GRANT SELECT ON healthcare_proc.patients TO biai;
GRANT SELECT ON healthcare_proc.appointments TO biai;
GRANT SELECT ON healthcare_proc.treatments TO biai;
GRANT SELECT ON healthcare_proc.lab_orders TO biai;
GRANT SELECT ON healthcare_proc.prescriptions TO biai;

-- Grant SELECT on all_constraints views (needed for PK/FK discovery)
GRANT SELECT ANY DICTIONARY TO biai;

COMMIT;
EXIT;
