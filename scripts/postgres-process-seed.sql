-- BIAI Process Test Data - PostgreSQL
-- 4 business process tables with realistic transition data
-- Depends on: postgres-seed.sql (sales_regions, customers, products, employees, orders)

-- ============================================================
-- 1. ORDER FULFILLMENT PROCESS (~500 transitions for ~100 orders)
-- ============================================================
CREATE TABLE IF NOT EXISTS order_process_log (
    process_id      SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    from_status     VARCHAR(30),
    to_status       VARCHAR(30) NOT NULL,
    changed_by      INTEGER REFERENCES employees(employee_id),
    changed_at      TIMESTAMP NOT NULL,
    notes           VARCHAR(500),
    duration_minutes INTEGER
);

CREATE INDEX IF NOT EXISTS idx_opl_order ON order_process_log(order_id);
CREATE INDEX IF NOT EXISTS idx_opl_to_status ON order_process_log(to_status);
CREATE INDEX IF NOT EXISTS idx_opl_changed_at ON order_process_log(changed_at);

-- Generate process transitions for delivered/shipped orders
DO $$
DECLARE
    v_stages TEXT[] := ARRAY['order_placed','payment_pending','payment_confirmed',
        'warehouse_assigned','picking','packing','shipped','in_transit','delivered'];
    v_notes TEXT[] := ARRAY['Order received from customer','Awaiting payment confirmation',
        'Payment verified successfully','Assigned to warehouse region',
        'Items being picked from shelves','Order packed and labeled',
        'Handed to carrier','In transit to destination','Delivered to customer'];
    v_emp_pool INTEGER[] := ARRAY[21,22,23,24,30,11,12,13,14,15];
    v_ts TIMESTAMP;
    v_emp INTEGER;
    v_last_stage INTEGER;
    v_dur INTEGER;
    v_cnt INTEGER := 0;
    rec RECORD;
BEGIN
    FOR rec IN (
        SELECT order_id, order_date, status
        FROM orders
        WHERE status IN ('delivered','shipped','confirmed')
        ORDER BY order_id
        LIMIT 120
    ) LOOP
        v_ts := rec.order_date::timestamp + (random() * 8)::int * interval '1 hour';

        IF rec.status = 'delivered' THEN
            v_last_stage := 9;
        ELSIF rec.status = 'shipped' THEN
            v_last_stage := 7 + (random() * 2)::int;
        ELSE
            v_last_stage := 3 + (random() * 4)::int;
        END IF;

        FOR i IN 1..v_last_stage LOOP
            CASE i
                WHEN 1 THEN v_dur := 1 + (random() * 4)::int;
                WHEN 2 THEN v_dur := 5 + (random() * 55)::int;
                WHEN 3 THEN v_dur := 2 + (random() * 28)::int;
                WHEN 4 THEN v_dur := 10 + (random() * 110)::int;
                WHEN 5 THEN v_dur := 15 + (random() * 75)::int;
                WHEN 6 THEN v_dur := 60 + (random() * 420)::int;  -- packing BOTTLENECK
                WHEN 7 THEN v_dur := 10 + (random() * 50)::int;
                WHEN 8 THEN v_dur := 720 + (random() * 3600)::int;  -- in_transit
                WHEN 9 THEN v_dur := 5 + (random() * 25)::int;
                ELSE v_dur := 10;
            END CASE;

            v_emp := v_emp_pool[1 + (random() * 9)::int];

            INSERT INTO order_process_log (order_id, from_status, to_status, changed_by, changed_at, notes, duration_minutes)
            VALUES (
                rec.order_id,
                CASE WHEN i = 1 THEN NULL ELSE v_stages[i-1] END,
                v_stages[i],
                v_emp,
                v_ts,
                v_notes[i],
                v_dur
            );

            v_ts := v_ts + (v_dur * interval '1 minute');
            v_cnt := v_cnt + 1;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Order process log: % rows inserted', v_cnt;
END $$;

-- ============================================================
-- 2. SALES PIPELINE / CRM (~300 pipeline entries)
-- ============================================================
CREATE TABLE IF NOT EXISTS sales_pipeline (
    pipeline_id      SERIAL PRIMARY KEY,
    customer_id      INTEGER NOT NULL REFERENCES customers(customer_id),
    employee_id      INTEGER NOT NULL REFERENCES employees(employee_id),
    stage            VARCHAR(30) NOT NULL
        CHECK (stage IN ('lead','qualified','proposal','negotiation','closed_won','closed_lost')),
    entered_at       TIMESTAMP NOT NULL,
    expected_value   NUMERIC(12,2),
    probability      INTEGER CHECK (probability BETWEEN 0 AND 100),
    product_interest VARCHAR(200),
    notes            VARCHAR(500),
    deal_source      VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_sp_customer ON sales_pipeline(customer_id);
CREATE INDEX IF NOT EXISTS idx_sp_stage ON sales_pipeline(stage);
CREATE INDEX IF NOT EXISTS idx_sp_employee ON sales_pipeline(employee_id);

CREATE TABLE IF NOT EXISTS pipeline_history (
    history_id   SERIAL PRIMARY KEY,
    pipeline_id  INTEGER NOT NULL,
    from_stage   VARCHAR(30),
    to_stage     VARCHAR(30) NOT NULL,
    changed_at   TIMESTAMP NOT NULL,
    changed_by   INTEGER REFERENCES employees(employee_id),
    notes        VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_ph_pipeline ON pipeline_history(pipeline_id);

DO $$
DECLARE
    v_stages TEXT[] := ARRAY['lead','qualified','proposal','negotiation','closed_won','closed_lost'];
    v_probs INTEGER[] := ARRAY[10,25,50,75,100,0];
    v_sources TEXT[] := ARRAY['Website','Referral','Trade Show','Cold Call','Partner','Inbound Marketing'];
    v_products TEXT[] := ARRAY['Enterprise Analytics Suite','Cloud Data Warehouse License',
        'BI Dashboard Pro','Implementation Consulting','ML Model Server',
        'Data Integration Platform','Enterprise Plan','Security Audit'];
    v_loss_reasons TEXT[] := ARRAY['Lost - budget constraints','Lost - competitor chosen','Lost - project cancelled','Lost - no response'];

    v_cust_id INTEGER;
    v_emp_id INTEGER;
    v_final INTEGER;
    v_ts TIMESTAMP;
    v_val NUMERIC(12,2);
    v_prod TEXT;
    v_src TEXT;
    v_pid INTEGER;
    v_rnd FLOAT;
    v_dur_hours INTEGER;
BEGIN
    FOR i IN 1..300 LOOP
        v_cust_id := 1 + (random() * 99)::int;
        v_emp_id := 1 + (random() * 9)::int;
        v_ts := '2023-06-01'::timestamp + ((random() * 600)::int * interval '1 day')
                + ((random() * 14)::int * interval '1 hour');
        v_val := round((5000 + random() * 195000)::numeric, 2);
        v_prod := v_products[1 + (random() * 7)::int];
        v_src := v_sources[1 + (random() * 5)::int];

        v_rnd := random();
        IF v_rnd < 0.30 THEN
            v_final := 5; -- closed_won
        ELSIF v_rnd < 0.50 THEN
            -- closed_lost: determine where it fails
            v_rnd := random();
            IF v_rnd < 0.40 THEN v_final := 2;    -- lose at qualified
            ELSIF v_rnd < 0.75 THEN v_final := 3;  -- lose at proposal
            ELSE v_final := 4;                       -- lose at negotiation
            END IF;

            v_dur_hours := 24 + (random() * 144)::int;

            INSERT INTO sales_pipeline (customer_id, employee_id, stage, entered_at, expected_value,
                probability, product_interest, notes, deal_source)
            VALUES (v_cust_id, v_emp_id, 'closed_lost',
                v_ts + (v_final * v_dur_hours * interval '1 hour'),
                v_val, 0, v_prod,
                v_loss_reasons[1 + (random() * 3)::int],
                v_src)
            RETURNING pipeline_id INTO v_pid;

            FOR j IN 1..v_final LOOP
                v_dur_hours := 24 + (random() * 144)::int;
                INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
                VALUES (v_pid,
                    CASE WHEN j = 1 THEN NULL ELSE v_stages[j-1] END,
                    v_stages[j],
                    v_ts + ((j-1) * v_dur_hours * interval '1 hour'),
                    v_emp_id, 'Stage transition');
            END LOOP;
            v_dur_hours := 24 + (random() * 144)::int;
            INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
            VALUES (v_pid, v_stages[v_final], 'closed_lost',
                v_ts + (v_final * v_dur_hours * interval '1 hour'),
                v_emp_id, 'Deal lost');

            CONTINUE;
        ELSIF v_rnd < 0.65 THEN v_final := 4;
        ELSIF v_rnd < 0.80 THEN v_final := 3;
        ELSIF v_rnd < 0.92 THEN v_final := 2;
        ELSE v_final := 1;
        END IF;

        -- Won or still active deals
        v_dur_hours := 24 + (random() * 96)::int;

        INSERT INTO sales_pipeline (customer_id, employee_id, stage, entered_at, expected_value,
            probability, product_interest, notes, deal_source)
        VALUES (v_cust_id, v_emp_id, v_stages[v_final],
            v_ts + (v_final * v_dur_hours * interval '1 hour'),
            v_val, v_probs[v_final], v_prod,
            CASE v_final WHEN 5 THEN 'Deal closed successfully' ELSE 'In progress' END,
            v_src)
        RETURNING pipeline_id INTO v_pid;

        FOR j IN 1..v_final LOOP
            v_dur_hours := 24 + (random() * 96)::int;
            INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
            VALUES (v_pid,
                CASE WHEN j = 1 THEN NULL ELSE v_stages[j-1] END,
                v_stages[j],
                v_ts + ((j-1) * v_dur_hours * interval '1 hour'),
                v_emp_id, 'Stage transition');
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Sales pipeline: 300 deals inserted';
END $$;

-- ============================================================
-- 3. SUPPORT TICKET WORKFLOW (~250 tickets)
-- ============================================================
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id    SERIAL PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    assigned_to  INTEGER REFERENCES employees(employee_id),
    priority     VARCHAR(5) NOT NULL CHECK (priority IN ('P1','P2','P3','P4')),
    category     VARCHAR(50) NOT NULL,
    subject      VARCHAR(200) NOT NULL,
    status       VARCHAR(30) NOT NULL
        CHECK (status IN ('new','assigned','investigating','waiting_customer','in_progress','resolved','closed','reopened')),
    created_at   TIMESTAMP NOT NULL,
    updated_at   TIMESTAMP NOT NULL,
    resolved_at  TIMESTAMP,
    resolution_minutes INTEGER
);

CREATE INDEX IF NOT EXISTS idx_st_customer ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_st_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_st_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_st_assigned ON support_tickets(assigned_to);

CREATE TABLE IF NOT EXISTS ticket_history (
    history_id   SERIAL PRIMARY KEY,
    ticket_id    INTEGER NOT NULL,
    from_status  VARCHAR(30),
    to_status    VARCHAR(30) NOT NULL,
    changed_by   INTEGER REFERENCES employees(employee_id),
    changed_at   TIMESTAMP NOT NULL,
    notes        VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_th_ticket ON ticket_history(ticket_id);

DO $$
DECLARE
    v_categories TEXT[] := ARRAY['Login Issue','Performance','Data Error','Integration',
        'Billing','Feature Request','Bug Report','Configuration','Access Control','Documentation'];
    v_subjects TEXT[] := ARRAY['Cannot log in after password reset','Dashboard loading slowly',
        'Incorrect data in monthly report','API integration returning 500 errors',
        'Invoice discrepancy for last month','Need export to CSV feature',
        'Charts not rendering on mobile','Custom field not saving values',
        'User permissions not applying correctly','API documentation outdated'];
    v_priorities TEXT[] := ARRAY['P1','P2','P3','P4'];
    v_support_emp INTEGER[] := ARRAY[21,22,23,24];

    v_tid INTEGER;
    v_cust_id INTEGER;
    v_emp_id INTEGER;
    v_priority TEXT;
    v_cat TEXT;
    v_subj TEXT;
    v_ts TIMESTAMP;
    v_cur_ts TIMESTAMP;
    v_final_st TEXT;
    v_rnd FLOAT;
    v_res_min INTEGER;
    v_wait_min INTEGER;
    v_done BOOLEAN;
BEGIN
    FOR i IN 1..250 LOOP
        v_cust_id := 1 + (random() * 99)::int;
        v_emp_id := v_support_emp[1 + (random() * 3)::int];
        v_priority := v_priorities[1 + (random() * 3)::int];
        v_cat := v_categories[1 + (random() * 9)::int];
        v_subj := v_subjects[1 + (random() * 9)::int];
        v_ts := '2024-01-01'::timestamp + ((random() * 400)::int * interval '1 day')
                + ((8 + (random() * 10)::int) * interval '1 hour');

        v_rnd := random();
        IF v_rnd < 0.60 THEN v_final_st := 'closed';
        ELSIF v_rnd < 0.75 THEN v_final_st := 'resolved';
        ELSIF v_rnd < 0.85 THEN v_final_st := 'in_progress';
        ELSIF v_rnd < 0.90 THEN v_final_st := 'waiting_customer';
        ELSIF v_rnd < 0.95 THEN v_final_st := 'investigating';
        ELSIF v_rnd < 0.98 THEN v_final_st := 'reopened';
        ELSE v_final_st := 'new';
        END IF;

        CASE v_priority
            WHEN 'P1' THEN v_res_min := 30 + (random() * 210)::int;
            WHEN 'P2' THEN v_res_min := 120 + (random() * 1320)::int;
            WHEN 'P3' THEN v_res_min := 480 + (random() * 3840)::int;
            WHEN 'P4' THEN v_res_min := 1440 + (random() * 8640)::int;
            ELSE v_res_min := 1440;
        END CASE;

        INSERT INTO support_tickets (customer_id, assigned_to, priority, category, subject, status,
            created_at, updated_at, resolved_at, resolution_minutes)
        VALUES (
            v_cust_id,
            CASE WHEN v_final_st = 'new' THEN NULL ELSE v_emp_id END,
            v_priority, v_cat, v_subj, v_final_st,
            v_ts,
            v_ts + (v_res_min * interval '1 minute'),
            CASE WHEN v_final_st IN ('resolved','closed') THEN v_ts + (v_res_min * interval '1 minute') ELSE NULL END,
            CASE WHEN v_final_st IN ('resolved','closed') THEN v_res_min ELSE NULL END
        ) RETURNING ticket_id INTO v_tid;

        v_cur_ts := v_ts;
        v_done := false;

        -- Step 1: new
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, NULL, 'new', NULL, v_cur_ts, 'Ticket created by customer');

        IF v_final_st = 'new' THEN CONTINUE; END IF;

        -- Step 2: assigned
        v_wait_min := 5 + (random() * 115)::int;
        v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, 'new', 'assigned', v_emp_id, v_cur_ts, 'Assigned to support engineer');

        IF v_final_st = 'assigned' THEN CONTINUE; END IF;

        -- Step 3: investigating
        v_wait_min := 15 + (random() * 165)::int;
        v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, 'assigned', 'investigating', v_emp_id, v_cur_ts, 'Investigation started');

        IF v_final_st = 'investigating' THEN CONTINUE; END IF;

        -- Step 4: sometimes waiting_customer (40%)
        IF random() < 0.40 THEN
            v_wait_min := 30 + (random() * 210)::int;
            v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'investigating', 'waiting_customer', v_emp_id, v_cur_ts, 'Awaiting customer response');

            IF v_final_st = 'waiting_customer' THEN CONTINUE; END IF;

            v_wait_min := 60 + (random() * 2820)::int;
            v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'waiting_customer', 'in_progress', v_emp_id, v_cur_ts, 'Customer responded, work resumed');
        ELSE
            v_wait_min := 30 + (random() * 90)::int;
            v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'investigating', 'in_progress', v_emp_id, v_cur_ts, 'Fix in progress');
        END IF;

        IF v_final_st = 'in_progress' THEN CONTINUE; END IF;

        -- Step 5: resolved
        v_wait_min := 30 + (random() * 450)::int;
        v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
        INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
        VALUES (v_tid, 'in_progress', 'resolved', v_emp_id, v_cur_ts, 'Issue resolved');

        IF v_final_st = 'resolved' THEN CONTINUE; END IF;

        -- Step 6: reopened (for some tickets)
        IF v_final_st = 'reopened' OR (v_final_st = 'closed' AND random() < 0.08) THEN
            v_wait_min := 120 + (random() * 4200)::int;
            v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'resolved', 'reopened', NULL, v_cur_ts, 'Customer reported issue persists');

            IF v_final_st = 'reopened' THEN CONTINUE; END IF;

            v_wait_min := 60 + (random() * 420)::int;
            v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'reopened', 'resolved', v_emp_id, v_cur_ts, 'Issue re-resolved');
        END IF;

        -- Step 7: closed
        IF v_final_st = 'closed' THEN
            v_wait_min := 1440 + (random() * 2880)::int;
            v_cur_ts := v_cur_ts + (v_wait_min * interval '1 minute');
            INSERT INTO ticket_history (ticket_id, from_status, to_status, changed_by, changed_at, notes)
            VALUES (v_tid, 'resolved', 'closed', v_emp_id, v_cur_ts, 'Ticket closed after confirmation');
        END IF;
    END LOOP;

    RAISE NOTICE 'Support tickets: 250 tickets inserted';
END $$;

-- ============================================================
-- 4. APPROVAL WORKFLOW (~200 requests)
-- ============================================================
CREATE TABLE IF NOT EXISTS approval_requests (
    request_id    SERIAL PRIMARY KEY,
    requester_id  INTEGER NOT NULL REFERENCES employees(employee_id),
    request_type  VARCHAR(30) NOT NULL
        CHECK (request_type IN ('purchase','travel','hiring','budget','expense')),
    description   VARCHAR(500) NOT NULL,
    amount        NUMERIC(12,2) NOT NULL,
    current_step  VARCHAR(30) NOT NULL
        CHECK (current_step IN ('draft','submitted','level1_review','level2_review','approved','rejected','executed')),
    status        VARCHAR(20) NOT NULL
        CHECK (status IN ('active','completed','rejected','cancelled')),
    created_at    TIMESTAMP NOT NULL,
    updated_at    TIMESTAMP NOT NULL,
    completed_at  TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ar_requester ON approval_requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_ar_type ON approval_requests(request_type);
CREATE INDEX IF NOT EXISTS idx_ar_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_ar_step ON approval_requests(current_step);

CREATE TABLE IF NOT EXISTS approval_steps (
    step_id       SERIAL PRIMARY KEY,
    request_id    INTEGER NOT NULL,
    step_name     VARCHAR(30) NOT NULL,
    approver_id   INTEGER REFERENCES employees(employee_id),
    action        VARCHAR(20) CHECK (action IN ('approve','reject','return','pending')),
    acted_at      TIMESTAMP,
    comments      VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_as_request ON approval_steps(request_id);
CREATE INDEX IF NOT EXISTS idx_as_approver ON approval_steps(approver_id);

DO $$
DECLARE
    v_types TEXT[] := ARRAY['purchase','travel','hiring','budget','expense'];
    v_descriptions TEXT[] := ARRAY[
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
    ];
    v_level1 INTEGER[] := ARRAY[1,2,3,11,17,21,25,28];
    v_level2 INTEGER[] := ARRAY[1,11,17,21,25,30];

    v_req_id INTEGER;
    v_emp_id INTEGER;
    v_type TEXT;
    v_desc TEXT;
    v_amount NUMERIC(12,2);
    v_ts TIMESTAMP;
    v_cur_ts TIMESTAMP;
    v_final_step TEXT;
    v_status TEXT;
    v_l1 INTEGER;
    v_l2 INTEGER;
    v_rnd FLOAT;
    v_wait INTEGER;
BEGIN
    FOR i IN 1..200 LOOP
        v_emp_id := 1 + (random() * 29)::int;
        v_type := v_types[1 + (random() * 4)::int];
        v_desc := v_descriptions[1 + (random() * 14)::int];
        v_l1 := v_level1[1 + (random() * 7)::int];
        v_l2 := v_level2[1 + (random() * 5)::int];

        CASE v_type
            WHEN 'purchase' THEN v_amount := round((500 + random() * 49500)::numeric, 2);
            WHEN 'travel'   THEN v_amount := round((200 + random() * 7800)::numeric, 2);
            WHEN 'hiring'   THEN v_amount := round((50000 + random() * 130000)::numeric, 2);
            WHEN 'budget'   THEN v_amount := round((10000 + random() * 490000)::numeric, 2);
            WHEN 'expense'  THEN v_amount := round((50 + random() * 4950)::numeric, 2);
            ELSE v_amount := 1000;
        END CASE;

        v_ts := '2024-01-01'::timestamp + ((random() * 400)::int * interval '1 day')
                + ((8 + (random() * 9)::int) * interval '1 hour');

        v_rnd := random();
        IF v_amount > 20000 THEN
            IF v_rnd < 0.20 THEN v_final_step := 'rejected'; v_status := 'rejected';
            ELSIF v_rnd < 0.85 THEN v_final_step := 'executed'; v_status := 'completed';
            ELSIF v_rnd < 0.92 THEN v_final_step := 'approved'; v_status := 'active';
            ELSE v_final_step := 'level2_review'; v_status := 'active';
            END IF;
        ELSIF v_amount < 5000 THEN
            IF v_rnd < 0.08 THEN v_final_step := 'rejected'; v_status := 'rejected';
            ELSIF v_rnd < 0.80 THEN v_final_step := 'executed'; v_status := 'completed';
            ELSIF v_rnd < 0.90 THEN v_final_step := 'approved'; v_status := 'active';
            ELSE v_final_step := 'level1_review'; v_status := 'active';
            END IF;
        ELSE
            IF v_rnd < 0.12 THEN v_final_step := 'rejected'; v_status := 'rejected';
            ELSIF v_rnd < 0.82 THEN v_final_step := 'executed'; v_status := 'completed';
            ELSIF v_rnd < 0.92 THEN v_final_step := 'approved'; v_status := 'active';
            ELSE v_final_step := 'level1_review'; v_status := 'active';
            END IF;
        END IF;

        v_cur_ts := v_ts;

        INSERT INTO approval_requests (requester_id, request_type, description, amount,
            current_step, status, created_at, updated_at, completed_at)
        VALUES (
            v_emp_id, v_type, v_desc, v_amount,
            v_final_step, v_status, v_ts,
            v_ts + ((60 + (random() * 10020)::int) * interval '1 minute'),
            CASE WHEN v_status IN ('completed','rejected') THEN
                v_ts + ((60 + (random() * 10020)::int) * interval '1 minute')
            ELSE NULL END
        ) RETURNING request_id INTO v_req_id;

        -- Step 1: draft -> submitted
        INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
        VALUES (v_req_id, 'draft', v_emp_id, 'approve', v_cur_ts, 'Request drafted');

        v_wait := 5 + (random() * 115)::int;
        v_cur_ts := v_cur_ts + (v_wait * interval '1 minute');

        INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
        VALUES (v_req_id, 'submitted', v_emp_id, 'approve', v_cur_ts, 'Submitted for approval');

        IF v_final_step = 'submitted' THEN CONTINUE; END IF;

        -- Step 2: level1_review
        v_wait := 60 + (random() * 2820)::int;
        v_cur_ts := v_cur_ts + (v_wait * interval '1 minute');

        IF v_final_step = 'rejected' AND v_amount < 5000 THEN
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'level1_review', v_l1, 'reject', v_cur_ts, 'Budget insufficient');
            CONTINUE;
        ELSE
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'level1_review', v_l1, 'approve', v_cur_ts, 'Approved at level 1');
        END IF;

        IF v_final_step = 'level1_review' THEN CONTINUE; END IF;

        -- Step 3: level2_review (for amounts > 5000 or hiring)
        IF v_amount > 5000 OR v_type = 'hiring' THEN
            v_wait := 120 + (random() * 4200)::int;
            v_cur_ts := v_cur_ts + (v_wait * interval '1 minute');

            IF v_final_step = 'rejected' THEN
                INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
                VALUES (v_req_id, 'level2_review', v_l2, 'reject', v_cur_ts, 'Exceeds department budget');
                CONTINUE;
            ELSE
                INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
                VALUES (v_req_id, 'level2_review', v_l2, 'approve', v_cur_ts, 'Approved at level 2');
            END IF;

            IF v_final_step = 'level2_review' THEN CONTINUE; END IF;
        END IF;

        -- Step 4: approved
        IF v_final_step IN ('approved', 'executed') THEN
            v_wait := 5 + (random() * 55)::int;
            v_cur_ts := v_cur_ts + (v_wait * interval '1 minute');
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'approved', v_l2, 'approve', v_cur_ts, 'Final approval granted');
        END IF;

        IF v_final_step = 'approved' THEN CONTINUE; END IF;

        -- Step 5: executed
        IF v_final_step = 'executed' THEN
            v_wait := 60 + (random() * 2820)::int;
            v_cur_ts := v_cur_ts + (v_wait * interval '1 minute');
            INSERT INTO approval_steps (request_id, step_name, approver_id, action, acted_at, comments)
            VALUES (v_req_id, 'executed', v_emp_id, 'approve', v_cur_ts, 'Request executed');
        END IF;
    END LOOP;

    RAISE NOTICE 'Approval requests: 200 requests inserted';
END $$;

-- ============================================================
-- VIEWS for process analytics
-- ============================================================

CREATE OR REPLACE VIEW v_order_process_bottlenecks AS
SELECT
    to_status AS stage,
    COUNT(*) AS transition_count,
    ROUND(AVG(duration_minutes)::numeric, 1) AS avg_duration_min,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_minutes)::numeric, 1) AS median_duration_min,
    MAX(duration_minutes) AS max_duration_min,
    MIN(duration_minutes) AS min_duration_min
FROM order_process_log
GROUP BY to_status
ORDER BY AVG(duration_minutes) DESC;

CREATE OR REPLACE VIEW v_pipeline_funnel AS
SELECT
    stage,
    COUNT(*) AS deal_count,
    ROUND(SUM(expected_value), 2) AS total_value,
    ROUND(AVG(expected_value), 2) AS avg_deal_value,
    ROUND(AVG(probability)::numeric, 1) AS avg_probability
FROM sales_pipeline
GROUP BY stage
ORDER BY CASE stage
    WHEN 'lead' THEN 1 WHEN 'qualified' THEN 2 WHEN 'proposal' THEN 3
    WHEN 'negotiation' THEN 4 WHEN 'closed_won' THEN 5 WHEN 'closed_lost' THEN 6 END;

CREATE OR REPLACE VIEW v_ticket_sla_analysis AS
SELECT
    priority,
    status,
    COUNT(*) AS ticket_count,
    ROUND(AVG(resolution_minutes)::numeric, 0) AS avg_resolution_min,
    ROUND((AVG(resolution_minutes) / 60.0)::numeric, 1) AS avg_resolution_hours
FROM support_tickets
WHERE resolution_minutes IS NOT NULL
GROUP BY priority, status
ORDER BY priority, status;

CREATE OR REPLACE VIEW v_approval_efficiency AS
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

CREATE OR REPLACE VIEW v_support_workload AS
SELECT
    e.first_name || ' ' || e.last_name AS engineer_name,
    e.title,
    COUNT(t.ticket_id) AS total_tickets,
    SUM(CASE WHEN t.status IN ('new','assigned','investigating','in_progress','waiting_customer','reopened') THEN 1 ELSE 0 END) AS open_tickets,
    SUM(CASE WHEN t.status IN ('resolved','closed') THEN 1 ELSE 0 END) AS resolved_tickets,
    ROUND(AVG(t.resolution_minutes)::numeric, 0) AS avg_resolution_min
FROM employees e
LEFT JOIN support_tickets t ON e.employee_id = t.assigned_to
WHERE e.department = 'Support'
GROUP BY e.employee_id, e.first_name, e.last_name, e.title;
