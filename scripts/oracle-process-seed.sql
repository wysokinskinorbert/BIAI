-- BIAI Process Test Data - Oracle
-- 4 business process tables with realistic transition data
-- Depends on: oracle-seed.sql (sales_regions, customers, products, employees, orders)
-- Run as biai user in XEPDB1

CONNECT biai/biai123@XEPDB1

-- ============================================================
-- 1. ORDER FULFILLMENT PROCESS (~500 transitions for ~100 orders)
-- Tracks order state transitions through fulfillment pipeline
-- ============================================================
CREATE TABLE order_process_log (
    process_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id        NUMBER NOT NULL REFERENCES orders(order_id),
    from_status     VARCHAR2(30),
    to_status       VARCHAR2(30) NOT NULL,
    changed_by      NUMBER REFERENCES employees(employee_id),
    changed_at      TIMESTAMP NOT NULL,
    notes           VARCHAR2(500),
    duration_minutes NUMBER
);

CREATE INDEX idx_opl_order ON order_process_log(order_id);
CREATE INDEX idx_opl_to_status ON order_process_log(to_status);
CREATE INDEX idx_opl_changed_at ON order_process_log(changed_at);

-- Generate ~500 process transitions for first 100 delivered/shipped orders
DECLARE
    TYPE str_arr IS VARRAY(9) OF VARCHAR2(30);
    v_stages str_arr := str_arr(
        'order_placed', 'payment_pending', 'payment_confirmed',
        'warehouse_assigned', 'picking', 'packing',
        'shipped', 'in_transit', 'delivered'
    );

    TYPE notes_arr IS VARRAY(9) OF VARCHAR2(200);
    v_notes notes_arr := notes_arr(
        'Order received from customer',
        'Awaiting payment confirmation',
        'Payment verified successfully',
        'Assigned to warehouse region',
        'Items being picked from shelves',
        'Order packed and labeled',
        'Handed to carrier',
        'In transit to destination',
        'Delivered to customer'
    );

    v_ts           TIMESTAMP;
    v_emp          NUMBER;
    v_last_stage   NUMBER;
    v_dur          NUMBER;
    v_cnt          NUMBER := 0;
    v_idx          NUMBER;
    v_from_status  VARCHAR2(30);

    -- Warehouse/operations employees: 21-24 (Support), 30 (Operations COO)
    -- Sales employees: 1-10
    TYPE emp_pool IS VARRAY(10) OF NUMBER;
    v_warehouse_emp emp_pool := emp_pool(21, 22, 23, 24, 30, 11, 12, 13, 14, 15);
BEGIN
    -- Process orders with status delivered or shipped (IDs 1..200 to get ~100 qualifying)
    FOR rec IN (
        SELECT order_id, order_date, status
        FROM orders
        WHERE status IN ('delivered', 'shipped', 'confirmed')
        AND ROWNUM <= 120
        ORDER BY order_id
    ) LOOP
        -- Start timestamp: order_date + random hours
        v_ts := CAST(rec.order_date AS TIMESTAMP) + NUMTODSINTERVAL(MOD(ABS(DBMS_RANDOM.RANDOM), 8), 'HOUR');

        -- Decide how far the order progresses
        IF rec.status = 'delivered' THEN
            v_last_stage := 9; -- all the way
        ELSIF rec.status = 'shipped' THEN
            v_last_stage := 7 + MOD(ABS(DBMS_RANDOM.RANDOM), 2); -- shipped or in_transit
        ELSE
            v_last_stage := 3 + MOD(ABS(DBMS_RANDOM.RANDOM), 4); -- confirmed: stops somewhere mid
        END IF;

        FOR i IN 1..v_last_stage LOOP
            -- Duration: early stages fast (5-30 min), packing is bottleneck (60-480 min), transit slow (720-4320 min)
            CASE i
                WHEN 1 THEN v_dur := 1 + MOD(ABS(DBMS_RANDOM.RANDOM), 4);      -- order_placed: instant
                WHEN 2 THEN v_dur := 5 + MOD(ABS(DBMS_RANDOM.RANDOM), 55);     -- payment_pending
                WHEN 3 THEN v_dur := 2 + MOD(ABS(DBMS_RANDOM.RANDOM), 28);     -- payment_confirmed
                WHEN 4 THEN v_dur := 10 + MOD(ABS(DBMS_RANDOM.RANDOM), 110);   -- warehouse_assigned
                WHEN 5 THEN v_dur := 15 + MOD(ABS(DBMS_RANDOM.RANDOM), 75);    -- picking
                WHEN 6 THEN v_dur := 60 + MOD(ABS(DBMS_RANDOM.RANDOM), 420);   -- packing (BOTTLENECK)
                WHEN 7 THEN v_dur := 10 + MOD(ABS(DBMS_RANDOM.RANDOM), 50);    -- shipped
                WHEN 8 THEN v_dur := 720 + MOD(ABS(DBMS_RANDOM.RANDOM), 3600); -- in_transit (0.5-3 days)
                WHEN 9 THEN v_dur := 5 + MOD(ABS(DBMS_RANDOM.RANDOM), 25);     -- delivered
                ELSE v_dur := 10;
            END CASE;

            v_idx := MOD(ABS(DBMS_RANDOM.RANDOM), v_warehouse_emp.COUNT) + 1;
            v_emp := v_warehouse_emp(v_idx);

            -- Use PL/SQL variable to avoid Oracle evaluating v_stages(0) in SQL CASE
            IF i = 1 THEN
                v_from_status := NULL;
            ELSE
                v_from_status := v_stages(i - 1);
            END IF;

            INSERT INTO order_process_log (
                order_id, from_status, to_status, changed_by, changed_at, notes, duration_minutes
            ) VALUES (
                rec.order_id,
                v_from_status,
                v_stages(i),
                v_emp,
                v_ts,
                v_notes(i),
                v_dur
            );

            v_ts := v_ts + NUMTODSINTERVAL(v_dur, 'MINUTE');
            v_cnt := v_cnt + 1;
        END LOOP;
    END LOOP;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Order process log: ' || v_cnt || ' rows inserted');
END;
/

-- ============================================================
-- 2. SALES PIPELINE / CRM (~300 pipeline entries)
-- Tracks sales opportunities through pipeline stages
-- ============================================================
CREATE TABLE sales_pipeline (
    pipeline_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id      NUMBER NOT NULL REFERENCES customers(customer_id),
    employee_id      NUMBER NOT NULL REFERENCES employees(employee_id),
    stage            VARCHAR2(30) NOT NULL
        CHECK (stage IN ('lead','qualified','proposal','negotiation','closed_won','closed_lost')),
    entered_at       TIMESTAMP NOT NULL,
    expected_value   NUMBER(12,2),
    probability      NUMBER(3) CHECK (probability BETWEEN 0 AND 100),
    product_interest VARCHAR2(200),
    notes            VARCHAR2(500),
    deal_source      VARCHAR2(50)
);

CREATE INDEX idx_sp_customer ON sales_pipeline(customer_id);
CREATE INDEX idx_sp_stage ON sales_pipeline(stage);
CREATE INDEX idx_sp_employee ON sales_pipeline(employee_id);

-- Also create a history table for stage transitions
CREATE TABLE pipeline_history (
    history_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_id  NUMBER NOT NULL,
    from_stage   VARCHAR2(30),
    to_stage     VARCHAR2(30) NOT NULL,
    changed_at   TIMESTAMP NOT NULL,
    changed_by   NUMBER REFERENCES employees(employee_id),
    notes        VARCHAR2(500)
);

CREATE INDEX idx_ph_pipeline ON pipeline_history(pipeline_id);

DECLARE
    TYPE str_arr IS VARRAY(6) OF VARCHAR2(30);
    v_stages str_arr := str_arr('lead','qualified','proposal','negotiation','closed_won','closed_lost');

    TYPE prob_arr IS VARRAY(6) OF NUMBER;
    v_probabilities prob_arr := prob_arr(10, 25, 50, 75, 100, 0);

    TYPE src_arr IS VARRAY(6) OF VARCHAR2(50);
    v_sources src_arr := src_arr('Website','Referral','Trade Show','Cold Call','Partner','Inbound Marketing');

    TYPE prod_arr IS VARRAY(8) OF VARCHAR2(200);
    v_products prod_arr := prod_arr(
        'Enterprise Analytics Suite',
        'Cloud Data Warehouse License',
        'BI Dashboard Pro',
        'Implementation Consulting',
        'ML Model Server',
        'Data Integration Platform',
        'Enterprise Plan',
        'Security Audit'
    );

    v_cust_id     NUMBER;
    v_emp_id      NUMBER;
    v_final       NUMBER;
    v_ts          TIMESTAMP;
    v_val         NUMBER(12,2);
    v_prod        VARCHAR2(200);
    v_src         VARCHAR2(50);
    v_pid         NUMBER;
    v_rnd         NUMBER;
    v_from_stage  VARCHAR2(30);
    v_loss_reason VARCHAR2(200);
    v_dur_hours   NUMBER;
BEGIN
    FOR i IN 1..300 LOOP
        v_cust_id := MOD(ABS(DBMS_RANDOM.RANDOM), 100) + 1;
        v_emp_id := MOD(ABS(DBMS_RANDOM.RANDOM), 10) + 1; -- sales employees 1-10
        v_ts := CAST(DATE '2023-06-01' + MOD(ABS(DBMS_RANDOM.RANDOM), 600) AS TIMESTAMP)
                + NUMTODSINTERVAL(MOD(ABS(DBMS_RANDOM.RANDOM), 14), 'HOUR');
        v_val := TRUNC(DBMS_RANDOM.VALUE(5000, 200000), 2);
        v_prod := v_products(MOD(ABS(DBMS_RANDOM.RANDOM), v_products.COUNT) + 1);
        v_src := v_sources(MOD(ABS(DBMS_RANDOM.RANDOM), v_sources.COUNT) + 1);

        -- Decide final stage: ~30% closed_won, ~20% closed_lost, rest still active
        v_rnd := DBMS_RANDOM.VALUE;
        IF v_rnd < 0.30 THEN
            v_final := 5; -- closed_won
        ELSIF v_rnd < 0.50 THEN
            v_final := 6; -- closed_lost
        ELSIF v_rnd < 0.65 THEN
            v_final := 4; -- negotiation (active)
        ELSIF v_rnd < 0.80 THEN
            v_final := 3; -- proposal (active)
        ELSIF v_rnd < 0.92 THEN
            v_final := 2; -- qualified (active)
        ELSE
            v_final := 1; -- lead (active)
        END IF;

        -- For closed_lost, stop at random earlier stage then jump to lost
        IF v_final = 6 THEN
            -- Lost deals: fail at qualified(40%), proposal(35%), negotiation(25%)
            v_rnd := DBMS_RANDOM.VALUE;
            IF v_rnd < 0.40 THEN
                v_final := 2; -- will lose at qualified
            ELSIF v_rnd < 0.75 THEN
                v_final := 3; -- will lose at proposal
            ELSE
                v_final := 4; -- will lose at negotiation
            END IF;

            -- Compute loss reason safely (avoid inline CASE with VARRAY)
            CASE MOD(ABS(DBMS_RANDOM.RANDOM), 4)
                WHEN 0 THEN v_loss_reason := 'Lost - budget constraints';
                WHEN 1 THEN v_loss_reason := 'Lost - competitor chosen';
                WHEN 2 THEN v_loss_reason := 'Lost - project cancelled';
                ELSE v_loss_reason := 'Lost - no response';
            END CASE;

            v_dur_hours := 24 + MOD(ABS(DBMS_RANDOM.RANDOM), 144);

            -- Insert pipeline at closed_lost
            INSERT INTO sales_pipeline (
                customer_id, employee_id, stage, entered_at, expected_value,
                probability, product_interest, notes, deal_source
            ) VALUES (
                v_cust_id, v_emp_id, 'closed_lost',
                v_ts + NUMTODSINTERVAL(v_final * v_dur_hours, 'HOUR'),
                v_val, 0, v_prod, v_loss_reason, v_src
            ) RETURNING pipeline_id INTO v_pid;

            -- History: transitions up to loss point + final loss
            FOR j IN 1..v_final LOOP
                -- Use PL/SQL variable to avoid Oracle evaluating v_stages(0) in SQL CASE
                IF j = 1 THEN
                    v_from_stage := NULL;
                ELSE
                    v_from_stage := v_stages(j - 1);
                END IF;
                v_dur_hours := 24 + MOD(ABS(DBMS_RANDOM.RANDOM), 144);
                INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
                VALUES (v_pid, v_from_stage, v_stages(j),
                    v_ts + NUMTODSINTERVAL((j-1) * v_dur_hours, 'HOUR'),
                    v_emp_id, 'Stage transition');
            END LOOP;
            v_dur_hours := 24 + MOD(ABS(DBMS_RANDOM.RANDOM), 144);
            INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
            VALUES (v_pid, v_stages(v_final), 'closed_lost',
                v_ts + NUMTODSINTERVAL(v_final * v_dur_hours, 'HOUR'),
                v_emp_id, 'Deal lost');

        ELSE
            -- Won or still active deals
            v_dur_hours := 24 + MOD(ABS(DBMS_RANDOM.RANDOM), 96);

            INSERT INTO sales_pipeline (
                customer_id, employee_id, stage, entered_at, expected_value,
                probability, product_interest, notes, deal_source
            ) VALUES (
                v_cust_id, v_emp_id,
                v_stages(v_final),
                v_ts + NUMTODSINTERVAL(v_final * v_dur_hours, 'HOUR'),
                v_val,
                v_probabilities(v_final),
                v_prod,
                CASE v_final WHEN 5 THEN 'Deal closed successfully' ELSE 'In progress' END,
                v_src
            ) RETURNING pipeline_id INTO v_pid;

            -- History: transitions through stages
            FOR j IN 1..v_final LOOP
                -- Use PL/SQL variable to avoid Oracle evaluating v_stages(0) in SQL CASE
                IF j = 1 THEN
                    v_from_stage := NULL;
                ELSE
                    v_from_stage := v_stages(j - 1);
                END IF;
                v_dur_hours := 24 + MOD(ABS(DBMS_RANDOM.RANDOM), 96);
                INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
                VALUES (v_pid, v_from_stage, v_stages(j),
                    v_ts + NUMTODSINTERVAL((j-1) * v_dur_hours, 'HOUR'),
                    v_emp_id, 'Stage transition');
            END LOOP;
        END IF;
    END LOOP;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Sales pipeline: 300 deals inserted');
END;
/

-- ============================================================
-- 3. SUPPORT TICKET WORKFLOW (~250 tickets, ~800 history records)
-- ============================================================
CREATE TABLE support_tickets (
    ticket_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id  NUMBER NOT NULL REFERENCES customers(customer_id),
    assigned_to  NUMBER REFERENCES employees(employee_id),
    priority     VARCHAR2(5) NOT NULL CHECK (priority IN ('P1','P2','P3','P4')),
    category     VARCHAR2(50) NOT NULL,
    subject      VARCHAR2(200) NOT NULL,
    status       VARCHAR2(30) NOT NULL
        CHECK (status IN ('new','assigned','investigating','waiting_customer','in_progress','resolved','closed','reopened')),
    created_at   TIMESTAMP NOT NULL,
    updated_at   TIMESTAMP NOT NULL,
    resolved_at  TIMESTAMP,
    resolution_minutes NUMBER
);

CREATE INDEX idx_st_customer ON support_tickets(customer_id);
CREATE INDEX idx_st_status ON support_tickets(status);
CREATE INDEX idx_st_priority ON support_tickets(priority);
CREATE INDEX idx_st_assigned ON support_tickets(assigned_to);

CREATE TABLE ticket_history (
    history_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id    NUMBER NOT NULL REFERENCES support_tickets(ticket_id),
    from_status  VARCHAR2(30),
    to_status    VARCHAR2(30) NOT NULL,
    changed_by   NUMBER REFERENCES employees(employee_id),
    changed_at   TIMESTAMP NOT NULL,
    notes        VARCHAR2(500)
);

CREATE INDEX idx_th_ticket ON ticket_history(ticket_id);

DECLARE
    TYPE str_arr IS VARRAY(10) OF VARCHAR2(50);
    v_categories str_arr := str_arr(
        'Login Issue','Performance','Data Error','Integration',
        'Billing','Feature Request','Bug Report','Configuration',
        'Access Control','Documentation'
    );

    TYPE subj_arr IS VARRAY(10) OF VARCHAR2(200);
    v_subjects subj_arr := subj_arr(
        'Cannot log in after password reset',
        'Dashboard loading slowly',
        'Incorrect data in monthly report',
        'API integration returning 500 errors',
        'Invoice discrepancy for last month',
        'Need export to CSV feature',
        'Charts not rendering on mobile',
        'Custom field not saving values',
        'User permissions not applying correctly',
        'API documentation outdated'
    );

    TYPE prior_arr IS VARRAY(4) OF VARCHAR2(5);
    v_priorities prior_arr := prior_arr('P1','P2','P3','P4');

    -- Support employees: 21 (Support Director), 22-24 (Support team)
    TYPE emp_pool IS VARRAY(4) OF NUMBER;
    v_support_emp emp_pool := emp_pool(21, 22, 23, 24);

    v_tid        NUMBER;
    v_cust_id    NUMBER;
    v_emp_id     NUMBER;
    v_priority   VARCHAR2(5);
    v_cat        VARCHAR2(50);
    v_subj       VARCHAR2(200);
    v_ts         TIMESTAMP;
    v_cur_ts     TIMESTAMP;
    v_final_st   VARCHAR2(30);
    v_rnd        NUMBER;
    v_res_min    NUMBER;
    v_wait_min   NUMBER;
BEGIN
    FOR i IN 1..250 LOOP
        v_cust_id := TRUNC(DBMS_RANDOM.VALUE(1, 101));
        v_emp_id := v_support_emp(TRUNC(DBMS_RANDOM.VALUE(1, v_support_emp.COUNT + 1)));
        v_priority := v_priorities(TRUNC(DBMS_RANDOM.VALUE(1, v_priorities.COUNT + 1)));
        v_cat := v_categories(TRUNC(DBMS_RANDOM.VALUE(1, v_categories.COUNT + 1)));
        v_subj := v_subjects(TRUNC(DBMS_RANDOM.VALUE(1, v_subjects.COUNT + 1)));
        v_ts := CAST(DATE '2024-01-01' + TRUNC(DBMS_RANDOM.VALUE(0, 400)) AS TIMESTAMP)
                + NUMTODSINTERVAL(TRUNC(DBMS_RANDOM.VALUE(8, 18)), 'HOUR');  -- business hours

        -- Decide final status: 60% closed, 15% resolved, 10% in_progress, 5% waiting_customer, 5% investigating, 3% reopened, 2% new
        v_rnd := DBMS_RANDOM.VALUE;
        IF v_rnd < 0.60 THEN
            v_final_st := 'closed';
        ELSIF v_rnd < 0.75 THEN
            v_final_st := 'resolved';
        ELSIF v_rnd < 0.85 THEN
            v_final_st := 'in_progress';
        ELSIF v_rnd < 0.90 THEN
            v_final_st := 'waiting_customer';
        ELSIF v_rnd < 0.95 THEN
            v_final_st := 'investigating';
        ELSIF v_rnd < 0.98 THEN
            v_final_st := 'reopened';
        ELSE
            v_final_st := 'new';
        END IF;

        -- Resolution time depends on priority: P1 fast, P4 slow
        CASE v_priority
            WHEN 'P1' THEN v_res_min := TRUNC(DBMS_RANDOM.VALUE(30, 240));      -- 30min-4h
            WHEN 'P2' THEN v_res_min := TRUNC(DBMS_RANDOM.VALUE(120, 1440));    -- 2h-1day
            WHEN 'P3' THEN v_res_min := TRUNC(DBMS_RANDOM.VALUE(480, 4320));    -- 8h-3days
            WHEN 'P4' THEN v_res_min := TRUNC(DBMS_RANDOM.VALUE(1440, 10080)); -- 1-7 days
            ELSE v_res_min := 1440;
        END CASE;

        -- Insert ticket
        INSERT INTO support_tickets (
            customer_id, assigned_to, priority, category, subject, status,
            created_at, updated_at, resolved_at, resolution_minutes
        ) VALUES (
            v_cust_id,
            CASE WHEN v_final_st = 'new' THEN NULL ELSE v_emp_id END,
            v_priority, v_cat, v_subj, v_final_st,
            v_ts,
            v_ts + NUMTODSINTERVAL(v_res_min, 'MINUTE'),
            CASE WHEN v_final_st IN ('resolved','closed') THEN v_ts + NUMTODSINTERVAL(v_res_min, 'MINUTE') ELSE NULL END,
            CASE WHEN v_final_st IN ('resolved','closed') THEN v_res_min ELSE NULL END
        ) RETURNING ticket_id INTO v_tid;

        -- Generate history transitions
        v_cur_ts := v_ts;

        -- Step 1: new
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, NULL, 'new', NULL, v_cur_ts, 'Ticket created by customer');

        IF v_final_st = 'new' THEN
            GOTO next_ticket;
        END IF;

        -- Step 2: assigned
        v_wait_min := TRUNC(DBMS_RANDOM.VALUE(5, 120));
        v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, 'new', 'assigned', v_emp_id, v_cur_ts, 'Assigned to support engineer');

        IF v_final_st = 'assigned' THEN
            GOTO next_ticket;
        END IF;

        -- Step 3: investigating
        v_wait_min := TRUNC(DBMS_RANDOM.VALUE(15, 180));
        v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, 'assigned', 'investigating', v_emp_id, v_cur_ts, 'Investigation started');

        IF v_final_st = 'investigating' THEN
            GOTO next_ticket;
        END IF;

        -- Step 4: sometimes waiting_customer (40% of tickets)
        IF DBMS_RANDOM.VALUE < 0.40 THEN
            v_wait_min := TRUNC(DBMS_RANDOM.VALUE(30, 240));
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'investigating', 'waiting_customer', v_emp_id, v_cur_ts, 'Awaiting customer response');

            IF v_final_st = 'waiting_customer' THEN
                GOTO next_ticket;
            END IF;

            -- Customer responds
            v_wait_min := TRUNC(DBMS_RANDOM.VALUE(60, 2880)); -- 1h-2days
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'waiting_customer', 'in_progress', v_emp_id, v_cur_ts, 'Customer responded, work resumed');
        ELSE
            -- Direct to in_progress
            v_wait_min := TRUNC(DBMS_RANDOM.VALUE(30, 120));
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'investigating', 'in_progress', v_emp_id, v_cur_ts, 'Fix in progress');
        END IF;

        IF v_final_st = 'in_progress' THEN
            GOTO next_ticket;
        END IF;

        -- Step 5: resolved
        v_wait_min := TRUNC(DBMS_RANDOM.VALUE(30, 480));
        v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, 'in_progress', 'resolved', v_emp_id, v_cur_ts, 'Issue resolved');

        IF v_final_st = 'resolved' THEN
            GOTO next_ticket;
        END IF;

        -- Step 6: reopened (3% chance for resolved tickets going to closed)
        IF v_final_st = 'reopened' OR (v_final_st = 'closed' AND DBMS_RANDOM.VALUE < 0.08) THEN
            v_wait_min := TRUNC(DBMS_RANDOM.VALUE(120, 4320));
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'resolved', 'reopened', NULL, v_cur_ts, 'Customer reported issue persists');

            IF v_final_st = 'reopened' THEN
                GOTO next_ticket;
            END IF;

            -- Re-resolve and close
            v_wait_min := TRUNC(DBMS_RANDOM.VALUE(60, 480));
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'reopened', 'resolved', v_emp_id, v_cur_ts, 'Issue re-resolved');
        END IF;

        -- Step 7: closed
        IF v_final_st = 'closed' THEN
            v_wait_min := TRUNC(DBMS_RANDOM.VALUE(1440, 4320)); -- 1-3 days after resolved
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait_min, 'MINUTE');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'resolved', 'closed', v_emp_id, v_cur_ts, 'Ticket closed after confirmation');
        END IF;

        <<next_ticket>>
        NULL;
    END LOOP;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Support tickets: 250 tickets inserted');
END;
/

-- ============================================================
-- 4. APPROVAL WORKFLOW (~200 requests, ~600 approval steps)
-- ============================================================
CREATE TABLE approval_requests (
    request_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    requester_id  NUMBER NOT NULL REFERENCES employees(employee_id),
    request_type  VARCHAR2(30) NOT NULL
        CHECK (request_type IN ('purchase','travel','hiring','budget','expense')),
    description   VARCHAR2(500) NOT NULL,
    amount        NUMBER(12,2) NOT NULL,
    current_step  VARCHAR2(30) NOT NULL
        CHECK (current_step IN ('draft','submitted','level1_review','level2_review','approved','rejected','executed')),
    status        VARCHAR2(20) NOT NULL
        CHECK (status IN ('active','completed','rejected','cancelled')),
    created_at    TIMESTAMP NOT NULL,
    updated_at    TIMESTAMP NOT NULL,
    completed_at  TIMESTAMP
);

CREATE INDEX idx_ar_requester ON approval_requests(requester_id);
CREATE INDEX idx_ar_type ON approval_requests(request_type);
CREATE INDEX idx_ar_status ON approval_requests(status);
CREATE INDEX idx_ar_step ON approval_requests(current_step);

CREATE TABLE approval_steps (
    step_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id    NUMBER NOT NULL REFERENCES approval_requests(request_id),
    step_name     VARCHAR2(30) NOT NULL,
    approver_id   NUMBER REFERENCES employees(employee_id),
    action        VARCHAR2(20) CHECK (action IN ('approve','reject','return','pending')),
    acted_at      TIMESTAMP,
    comments      VARCHAR2(500)
);

CREATE INDEX idx_as_request ON approval_steps(request_id);
CREATE INDEX idx_as_approver ON approval_steps(approver_id);

DECLARE
    TYPE str_arr IS VARRAY(5) OF VARCHAR2(30);
    v_types str_arr := str_arr('purchase','travel','hiring','budget','expense');

    TYPE desc_arr IS VARRAY(15) OF VARCHAR2(500);
    v_descriptions desc_arr := desc_arr(
        'New server hardware for data center expansion',
        'Software license renewal - Enterprise Analytics',
        'Conference attendance - Tech Summit 2025',
        'Client visit to Tokyo office',
        'Hiring senior data engineer - backfill position',
        'Hiring junior developer - team expansion',
        'Annual marketing budget increase request',
        'Q3 project budget reallocation',
        'Team offsite meeting expenses',
        'New laptop replacement for engineering team',
        'Cloud infrastructure cost increase',
        'Training program for sales team',
        'Office supplies bulk order',
        'Consultant engagement for security audit',
        'Travel expenses for sales roadshow'
    );

    -- Level 1 approvers: managers (employees 1,2,3,11,17,21,25,28)
    TYPE mgr_arr IS VARRAY(8) OF NUMBER;
    v_level1 mgr_arr := mgr_arr(1, 2, 3, 11, 17, 21, 25, 28);

    -- Level 2 approvers: directors/C-suite (employees 1,11,17,21,25,30)
    TYPE dir_arr IS VARRAY(6) OF NUMBER;
    v_level2 dir_arr := dir_arr(1, 11, 17, 21, 25, 30);

    v_req_id     NUMBER;
    v_emp_id     NUMBER;
    v_type       VARCHAR2(30);
    v_desc       VARCHAR2(500);
    v_amount     NUMBER(12,2);
    v_ts         TIMESTAMP;
    v_cur_ts     TIMESTAMP;
    v_final_step VARCHAR2(30);
    v_status     VARCHAR2(20);
    v_l1         NUMBER;
    v_l2         NUMBER;
    v_rnd        NUMBER;
    v_wait       NUMBER;
BEGIN
    FOR i IN 1..200 LOOP
        v_emp_id := TRUNC(DBMS_RANDOM.VALUE(1, 31)); -- any employee
        v_type := v_types(TRUNC(DBMS_RANDOM.VALUE(1, v_types.COUNT + 1)));
        v_desc := v_descriptions(TRUNC(DBMS_RANDOM.VALUE(1, v_descriptions.COUNT + 1)));
        v_l1 := v_level1(TRUNC(DBMS_RANDOM.VALUE(1, v_level1.COUNT + 1)));
        v_l2 := v_level2(TRUNC(DBMS_RANDOM.VALUE(1, v_level2.COUNT + 1)));

        -- Amount depends on type
        CASE v_type
            WHEN 'purchase' THEN v_amount := TRUNC(DBMS_RANDOM.VALUE(500, 50000), 2);
            WHEN 'travel'   THEN v_amount := TRUNC(DBMS_RANDOM.VALUE(200, 8000), 2);
            WHEN 'hiring'   THEN v_amount := TRUNC(DBMS_RANDOM.VALUE(50000, 180000), 2);
            WHEN 'budget'   THEN v_amount := TRUNC(DBMS_RANDOM.VALUE(10000, 500000), 2);
            WHEN 'expense'  THEN v_amount := TRUNC(DBMS_RANDOM.VALUE(50, 5000), 2);
            ELSE v_amount := 1000;
        END CASE;

        v_ts := CAST(DATE '2024-01-01' + TRUNC(DBMS_RANDOM.VALUE(0, 400)) AS TIMESTAMP)
                + NUMTODSINTERVAL(TRUNC(DBMS_RANDOM.VALUE(8, 17)), 'HOUR');

        -- Decide final outcome
        -- High amounts (>20000): need level2, higher rejection rate (25%)
        -- Low amounts (<5000): level1 only, low rejection (10%)
        -- Medium: need level2, moderate rejection (15%)
        v_rnd := DBMS_RANDOM.VALUE;
        IF v_amount > 20000 THEN
            IF v_rnd < 0.20 THEN
                v_final_step := 'rejected';
                v_status := 'rejected';
            ELSIF v_rnd < 0.85 THEN
                v_final_step := 'executed';
                v_status := 'completed';
            ELSIF v_rnd < 0.92 THEN
                v_final_step := 'approved';
                v_status := 'active';
            ELSE
                v_final_step := 'level2_review';
                v_status := 'active';
            END IF;
        ELSIF v_amount < 5000 THEN
            IF v_rnd < 0.08 THEN
                v_final_step := 'rejected';
                v_status := 'rejected';
            ELSIF v_rnd < 0.80 THEN
                v_final_step := 'executed';
                v_status := 'completed';
            ELSIF v_rnd < 0.90 THEN
                v_final_step := 'approved';
                v_status := 'active';
            ELSE
                v_final_step := 'level1_review';
                v_status := 'active';
            END IF;
        ELSE
            IF v_rnd < 0.12 THEN
                v_final_step := 'rejected';
                v_status := 'rejected';
            ELSIF v_rnd < 0.82 THEN
                v_final_step := 'executed';
                v_status := 'completed';
            ELSIF v_rnd < 0.92 THEN
                v_final_step := 'approved';
                v_status := 'active';
            ELSE
                v_final_step := 'level1_review';
                v_status := 'active';
            END IF;
        END IF;

        v_cur_ts := v_ts;

        INSERT INTO approval_requests (
            requester_id, request_type, description, amount,
            current_step, status, created_at, updated_at, completed_at
        ) VALUES (
            v_emp_id, v_type, v_desc, v_amount,
            v_final_step, v_status, v_ts,
            v_ts + NUMTODSINTERVAL(TRUNC(DBMS_RANDOM.VALUE(60, 10080)), 'MINUTE'),
            CASE WHEN v_status IN ('completed','rejected') THEN
                v_ts + NUMTODSINTERVAL(TRUNC(DBMS_RANDOM.VALUE(60, 10080)), 'MINUTE')
            ELSE NULL END
        ) RETURNING request_id INTO v_req_id;

        -- Step 1: draft -> submitted
        INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
        VALUES (v_req_id, 'draft', v_emp_id, 'approve', v_cur_ts, 'Request drafted');

        v_wait := TRUNC(DBMS_RANDOM.VALUE(5, 120));
        v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait, 'MINUTE');

        INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
        VALUES (v_req_id, 'submitted', v_emp_id, 'approve', v_cur_ts, 'Submitted for approval');

        IF v_final_step = 'submitted' THEN
            GOTO next_request;
        END IF;

        -- Step 2: level1_review
        v_wait := TRUNC(DBMS_RANDOM.VALUE(60, 2880)); -- 1h to 2days
        v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait, 'MINUTE');

        IF v_final_step = 'rejected' AND v_amount < 5000 THEN
            -- Rejected at level 1
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'level1_review', v_l1, 'reject', v_cur_ts,
                CASE TRUNC(DBMS_RANDOM.VALUE(1,4))
                    WHEN 1 THEN 'Budget insufficient'
                    WHEN 2 THEN 'Not aligned with objectives'
                    ELSE 'Requires additional justification' END);
            GOTO next_request;
        ELSE
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'level1_review', v_l1, 'approve', v_cur_ts, 'Approved at level 1');
        END IF;

        IF v_final_step = 'level1_review' THEN
            GOTO next_request;
        END IF;

        -- Step 3: level2_review (for amounts > 5000 or hiring)
        IF v_amount > 5000 OR v_type = 'hiring' THEN
            v_wait := TRUNC(DBMS_RANDOM.VALUE(120, 4320)); -- 2h to 3days
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait, 'MINUTE');

            IF v_final_step = 'rejected' THEN
                INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
                VALUES (v_req_id, 'level2_review', v_l2, 'reject', v_cur_ts,
                    CASE TRUNC(DBMS_RANDOM.VALUE(1,4))
                        WHEN 1 THEN 'Exceeds department budget'
                        WHEN 2 THEN 'Postpone to next quarter'
                        ELSE 'Need cost-benefit analysis' END);
                GOTO next_request;
            ELSE
                INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
                VALUES (v_req_id, 'level2_review', v_l2, 'approve', v_cur_ts, 'Approved at level 2');
            END IF;

            IF v_final_step = 'level2_review' THEN
                GOTO next_request;
            END IF;
        END IF;

        -- Step 4: approved
        IF v_final_step IN ('approved', 'executed') THEN
            v_wait := TRUNC(DBMS_RANDOM.VALUE(5, 60));
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait, 'MINUTE');
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'approved', v_l2, 'approve', v_cur_ts, 'Final approval granted');
        END IF;

        IF v_final_step = 'approved' THEN
            GOTO next_request;
        END IF;

        -- Step 5: executed
        IF v_final_step = 'executed' THEN
            v_wait := TRUNC(DBMS_RANDOM.VALUE(60, 2880));
            v_cur_ts := v_cur_ts + NUMTODSINTERVAL(v_wait, 'MINUTE');
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'executed', v_emp_id, 'approve', v_cur_ts, 'Request executed');
        END IF;

        <<next_request>>
        NULL;
    END LOOP;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Approval requests: 200 requests inserted');
END;
/

-- ============================================================
-- VIEWS for process analytics
-- ============================================================

-- Order fulfillment bottleneck analysis
CREATE VIEW v_order_process_bottlenecks AS
SELECT
    to_status AS stage,
    COUNT(*) AS transition_count,
    ROUND(AVG(duration_minutes), 1) AS avg_duration_min,
    ROUND(MEDIAN(duration_minutes), 1) AS median_duration_min,
    MAX(duration_minutes) AS max_duration_min,
    MIN(duration_minutes) AS min_duration_min
FROM order_process_log
GROUP BY to_status
ORDER BY AVG(duration_minutes) DESC;

-- Sales pipeline conversion funnel
CREATE VIEW v_pipeline_funnel AS
SELECT
    stage,
    COUNT(*) AS deal_count,
    ROUND(SUM(expected_value), 2) AS total_value,
    ROUND(AVG(expected_value), 2) AS avg_deal_value,
    ROUND(AVG(probability), 1) AS avg_probability
FROM sales_pipeline
GROUP BY stage
ORDER BY DECODE(stage, 'lead',1,'qualified',2,'proposal',3,'negotiation',4,'closed_won',5,'closed_lost',6);

-- Support ticket SLA analysis
CREATE VIEW v_ticket_sla_analysis AS
SELECT
    priority,
    status,
    COUNT(*) AS ticket_count,
    ROUND(AVG(resolution_minutes), 0) AS avg_resolution_min,
    ROUND(AVG(resolution_minutes) / 60, 1) AS avg_resolution_hours
FROM support_tickets
WHERE resolution_minutes IS NOT NULL
GROUP BY priority, status
ORDER BY priority, status;

-- Approval workflow efficiency
CREATE VIEW v_approval_efficiency AS
SELECT
    request_type,
    current_step,
    status,
    COUNT(*) AS request_count,
    ROUND(AVG(amount), 2) AS avg_amount,
    ROUND(SUM(amount), 2) AS total_amount
FROM approval_requests
GROUP BY request_type, current_step, status
ORDER BY request_type, current_step;

-- Support ticket workload per employee
CREATE VIEW v_support_workload AS
SELECT
    e.first_name || ' ' || e.last_name AS engineer_name,
    e.title,
    COUNT(t.ticket_id) AS total_tickets,
    SUM(CASE WHEN t.status IN ('new','assigned','investigating','in_progress','waiting_customer','reopened') THEN 1 ELSE 0 END) AS open_tickets,
    SUM(CASE WHEN t.status IN ('resolved','closed') THEN 1 ELSE 0 END) AS resolved_tickets,
    ROUND(AVG(t.resolution_minutes), 0) AS avg_resolution_min
FROM employees e
LEFT JOIN support_tickets t ON e.employee_id = t.assigned_to
WHERE e.department = 'Support'
GROUP BY e.employee_id, e.first_name, e.last_name, e.title;

COMMIT;
