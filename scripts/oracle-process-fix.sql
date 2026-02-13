-- Fix for ORA-06532 in order_process_log and sales_pipeline
-- Uses LEAST() to guard VARRAY access from edge-case subscript overflow
-- Run as biai user in XEPDB1

-- Clean up failed tables
TRUNCATE TABLE pipeline_history;
TRUNCATE TABLE sales_pipeline;
TRUNCATE TABLE order_process_log;

-- ============================================================
-- 1. ORDER FULFILLMENT PROCESS (fixed)
-- ============================================================
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

    v_ts         TIMESTAMP;
    v_emp        NUMBER;
    v_last_stage NUMBER;
    v_dur        NUMBER;
    v_cnt        NUMBER := 0;
    v_idx        NUMBER;

    TYPE emp_pool IS VARRAY(10) OF NUMBER;
    v_warehouse_emp emp_pool := emp_pool(21, 22, 23, 24, 30, 11, 12, 13, 14, 15);
BEGIN
    FOR rec IN (
        SELECT order_id, order_date, status
        FROM orders
        WHERE status IN ('delivered', 'shipped', 'confirmed')
        AND ROWNUM <= 120
        ORDER BY order_id
    ) LOOP
        v_ts := CAST(rec.order_date AS TIMESTAMP) + NUMTODSINTERVAL(TRUNC(DBMS_RANDOM.VALUE(0, 8)), 'HOUR');

        IF rec.status = 'delivered' THEN
            v_last_stage := 9;
        ELSIF rec.status = 'shipped' THEN
            v_last_stage := LEAST(TRUNC(DBMS_RANDOM.VALUE(7, 9)), 8);
        ELSE
            v_last_stage := LEAST(TRUNC(DBMS_RANDOM.VALUE(3, 7)), 6);
        END IF;

        FOR i IN 1..v_last_stage LOOP
            CASE i
                WHEN 1 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(1, 5));
                WHEN 2 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(5, 60));
                WHEN 3 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(2, 30));
                WHEN 4 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(10, 120));
                WHEN 5 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(15, 90));
                WHEN 6 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(60, 480));
                WHEN 7 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(10, 60));
                WHEN 8 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(720, 4320));
                WHEN 9 THEN v_dur := TRUNC(DBMS_RANDOM.VALUE(5, 30));
                ELSE v_dur := 10;
            END CASE;

            v_idx := LEAST(TRUNC(DBMS_RANDOM.VALUE(1, v_warehouse_emp.COUNT + 1)), v_warehouse_emp.COUNT);
            v_emp := v_warehouse_emp(v_idx);

            INSERT INTO order_process_log (
                order_id, from_status, to_status, changed_by, changed_at, notes, duration_minutes
            ) VALUES (
                rec.order_id,
                CASE WHEN i = 1 THEN NULL ELSE v_stages(i - 1) END,
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
-- 2. SALES PIPELINE (fixed)
-- ============================================================
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

    v_cust_id   NUMBER;
    v_emp_id    NUMBER;
    v_final     NUMBER;
    v_ts        TIMESTAMP;
    v_val       NUMBER(12,2);
    v_prod      VARCHAR2(200);
    v_src       VARCHAR2(50);
    v_pid       NUMBER;
    v_rnd       NUMBER;
    v_idx       NUMBER;
    v_loss_reason VARCHAR2(100);
BEGIN
    FOR i IN 1..300 LOOP
        v_cust_id := LEAST(TRUNC(DBMS_RANDOM.VALUE(1, 101)), 100);
        v_emp_id := LEAST(TRUNC(DBMS_RANDOM.VALUE(1, 11)), 10);
        v_ts := CAST(DATE '2023-06-01' + TRUNC(DBMS_RANDOM.VALUE(0, 600)) AS TIMESTAMP)
                + NUMTODSINTERVAL(TRUNC(DBMS_RANDOM.VALUE(0, 14)), 'HOUR');
        v_val := TRUNC(DBMS_RANDOM.VALUE(5000, 200000), 2);

        v_idx := LEAST(TRUNC(DBMS_RANDOM.VALUE(1, v_products.COUNT + 1)), v_products.COUNT);
        v_prod := v_products(v_idx);

        v_idx := LEAST(TRUNC(DBMS_RANDOM.VALUE(1, v_sources.COUNT + 1)), v_sources.COUNT);
        v_src := v_sources(v_idx);

        -- Decide final stage
        v_rnd := DBMS_RANDOM.VALUE;
        IF v_rnd < 0.30 THEN
            v_final := 5; -- closed_won
        ELSIF v_rnd < 0.50 THEN
            v_final := 6; -- closed_lost
        ELSIF v_rnd < 0.65 THEN
            v_final := 4;
        ELSIF v_rnd < 0.80 THEN
            v_final := 3;
        ELSIF v_rnd < 0.92 THEN
            v_final := 2;
        ELSE
            v_final := 1;
        END IF;

        IF v_final = 6 THEN
            -- Lost deals
            v_rnd := DBMS_RANDOM.VALUE;
            IF v_rnd < 0.40 THEN
                v_final := 2;
            ELSIF v_rnd < 0.75 THEN
                v_final := 3;
            ELSE
                v_final := 4;
            END IF;

            -- Compute loss reason safely (no VARRAY involved, just CASE)
            v_idx := LEAST(TRUNC(DBMS_RANDOM.VALUE(1, 5)), 4);
            CASE v_idx
                WHEN 1 THEN v_loss_reason := 'Lost - budget constraints';
                WHEN 2 THEN v_loss_reason := 'Lost - competitor chosen';
                WHEN 3 THEN v_loss_reason := 'Lost - project cancelled';
                ELSE v_loss_reason := 'Lost - no response';
            END CASE;

            INSERT INTO sales_pipeline (
                customer_id, employee_id, stage, entered_at, expected_value,
                probability, product_interest, notes, deal_source
            ) VALUES (
                v_cust_id, v_emp_id, 'closed_lost',
                v_ts + NUMTODSINTERVAL(v_final * LEAST(TRUNC(DBMS_RANDOM.VALUE(24, 168)), 167), 'HOUR'),
                v_val, 0, v_prod, v_loss_reason, v_src
            ) RETURNING pipeline_id INTO v_pid;

            FOR j IN 1..v_final LOOP
                INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
                VALUES (v_pid,
                    CASE WHEN j = 1 THEN NULL ELSE v_stages(j-1) END,
                    v_stages(j),
                    v_ts + NUMTODSINTERVAL((j-1) * LEAST(TRUNC(DBMS_RANDOM.VALUE(24, 168)), 167), 'HOUR'),
                    v_emp_id, 'Stage transition');
            END LOOP;
            INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
            VALUES (v_pid, v_stages(v_final), 'closed_lost',
                v_ts + NUMTODSINTERVAL(v_final * LEAST(TRUNC(DBMS_RANDOM.VALUE(24, 168)), 167), 'HOUR'),
                v_emp_id, 'Deal lost');

        ELSE
            -- Won or still active deals
            INSERT INTO sales_pipeline (
                customer_id, employee_id, stage, entered_at, expected_value,
                probability, product_interest, notes, deal_source
            ) VALUES (
                v_cust_id, v_emp_id,
                v_stages(v_final),
                v_ts + NUMTODSINTERVAL(v_final * LEAST(TRUNC(DBMS_RANDOM.VALUE(24, 120)), 119), 'HOUR'),
                v_val,
                v_probabilities(v_final),
                v_prod,
                CASE v_final WHEN 5 THEN 'Deal closed successfully' ELSE 'In progress' END,
                v_src
            ) RETURNING pipeline_id INTO v_pid;

            FOR j IN 1..v_final LOOP
                INSERT INTO pipeline_history (pipeline_id, from_stage, to_stage, changed_at, changed_by, notes)
                VALUES (v_pid,
                    CASE WHEN j = 1 THEN NULL ELSE v_stages(j-1) END,
                    v_stages(j),
                    v_ts + NUMTODSINTERVAL((j-1) * LEAST(TRUNC(DBMS_RANDOM.VALUE(24, 120)), 119), 'HOUR'),
                    v_emp_id, 'Stage transition');
            END LOOP;
        END IF;
    END LOOP;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Sales pipeline: 300 deals inserted');
END;
/
