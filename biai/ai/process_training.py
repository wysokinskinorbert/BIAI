"""Process-specific training data for Vanna AI.

Provides domain documentation and example SQL queries for process tables:
- ORDER_PROCESS_LOG: Order fulfillment pipeline tracking
- SALES_PIPELINE + PIPELINE_HISTORY: CRM/sales opportunity tracking
- SUPPORT_TICKETS + TICKET_HISTORY: Support ticket workflow
- APPROVAL_REQUESTS + APPROVAL_STEPS: Multi-level approval workflow
"""

from biai.models.schema import SchemaSnapshot


# Table names we look for (upper-cased for matching)
PROCESS_TABLES = {
    "ORDER_PROCESS_LOG",
    "SALES_PIPELINE",
    "PIPELINE_HISTORY",
    "SUPPORT_TICKETS",
    "TICKET_HISTORY",
    "APPROVAL_REQUESTS",
    "APPROVAL_STEPS",
}

# Views created alongside process tables
PROCESS_VIEWS = {
    "V_ORDER_PROCESS_BOTTLENECKS",
    "V_PIPELINE_FUNNEL",
    "V_TICKET_SLA_ANALYSIS",
    "V_APPROVAL_EFFICIENCY",
    "V_SUPPORT_WORKLOAD",
}


def has_process_tables(schema: SchemaSnapshot) -> bool:
    """Check if schema contains any of the process tables."""
    table_names = {t.name.upper() for t in schema.tables}
    return bool(table_names & PROCESS_TABLES)


def get_process_documentation(schema: SchemaSnapshot) -> list[str]:
    """Generate domain-specific documentation for process tables found in schema."""
    table_names = {t.name.upper() for t in schema.tables}
    docs: list[str] = []

    if "ORDER_PROCESS_LOG" in table_names:
        docs.extend(_order_process_docs())

    if "SALES_PIPELINE" in table_names:
        docs.extend(_sales_pipeline_docs())

    if "SUPPORT_TICKETS" in table_names:
        docs.extend(_support_ticket_docs())

    if "APPROVAL_REQUESTS" in table_names:
        docs.extend(_approval_docs())

    # Cross-table relationships
    if len(table_names & PROCESS_TABLES) >= 2:
        docs.append(
            "Process tables share foreign keys to the EMPLOYEES table (employee_id) "
            "and CUSTOMERS table (customer_id). You can JOIN process tables with "
            "EMPLOYEES to get employee names (first_name, last_name, title, department) "
            "and with CUSTOMERS for customer details (company_name, contact_name)."
        )

    return docs


def get_process_examples(schema: SchemaSnapshot, is_oracle: bool = True) -> list[tuple[str, str]]:
    """Generate domain-specific example query pairs for process tables."""
    table_names = {t.name.upper() for t in schema.tables}
    examples: list[tuple[str, str]] = []
    limit = "FETCH FIRST {n} ROWS ONLY" if is_oracle else "LIMIT {n}"

    if "ORDER_PROCESS_LOG" in table_names:
        examples.extend(_order_process_examples(limit))

    if "SALES_PIPELINE" in table_names:
        examples.extend(_sales_pipeline_examples(limit))

    if "SUPPORT_TICKETS" in table_names:
        examples.extend(_support_ticket_examples(limit))

    if "APPROVAL_REQUESTS" in table_names:
        examples.extend(_approval_examples(limit))

    return examples


# ---------------------------------------------------------------------------
# ORDER PROCESS LOG
# ---------------------------------------------------------------------------

def _order_process_docs() -> list[str]:
    return [
        "ORDER_PROCESS_LOG tracks the fulfillment lifecycle of customer orders. "
        "Each row records a single state transition for an order. Columns: "
        "process_id (PK), order_id (FK to ORDERS), from_status (previous state or NULL for initial), "
        "to_status (new state), changed_by (FK to EMPLOYEES), changed_at (TIMESTAMP), "
        "notes (text), duration_minutes (time spent in the new stage). "
        "The order fulfillment stages in sequence are: order_placed, payment_pending, "
        "payment_confirmed, warehouse_assigned, picking, packing, shipped, in_transit, delivered.",

        "To find bottleneck stages in order fulfillment, GROUP BY to_status and "
        "compute AVG(duration_minutes). The packing stage is typically the slowest. "
        "To compute end-to-end order fulfillment time, SUM duration_minutes per order_id.",

        "The view V_ORDER_PROCESS_BOTTLENECKS provides pre-aggregated bottleneck analysis: "
        "stage, transition_count, avg_duration_min, median_duration_min, max_duration_min, min_duration_min.",
    ]


def _order_process_examples(limit: str) -> list[tuple[str, str]]:
    return [
        (
            "Show average duration of each stage in order fulfillment",
            "SELECT to_status AS stage, "
            "COUNT(*) AS transitions, "
            "ROUND(AVG(duration_minutes), 1) AS avg_duration_min, "
            "ROUND(MAX(duration_minutes), 1) AS max_duration_min "
            "FROM order_process_log "
            "GROUP BY to_status "
            "ORDER BY avg_duration_min DESC",
        ),
        (
            "Which stage is the biggest bottleneck in order processing?",
            "SELECT to_status AS stage, "
            "ROUND(AVG(duration_minutes), 1) AS avg_duration_min "
            "FROM order_process_log "
            "GROUP BY to_status "
            "ORDER BY avg_duration_min DESC " + limit.format(n=1),
        ),
        (
            "Show total fulfillment time per order",
            "SELECT order_id, "
            "SUM(duration_minutes) AS total_minutes, "
            "ROUND(SUM(duration_minutes) / 60.0, 1) AS total_hours, "
            "MIN(changed_at) AS started_at, "
            "MAX(changed_at) AS last_update "
            "FROM order_process_log "
            "GROUP BY order_id "
            "ORDER BY total_minutes DESC " + limit.format(n=20),
        ),
        (
            "How many orders are currently at each stage?",
            "SELECT opl.to_status AS current_stage, COUNT(DISTINCT opl.order_id) AS order_count "
            "FROM order_process_log opl "
            "INNER JOIN ("
            "  SELECT order_id, MAX(changed_at) AS max_ts "
            "  FROM order_process_log GROUP BY order_id"
            ") latest ON opl.order_id = latest.order_id AND opl.changed_at = latest.max_ts "
            "GROUP BY opl.to_status "
            "ORDER BY order_count DESC",
        ),
        (
            "Show order process transitions with employee names",
            "SELECT opl.order_id, opl.from_status, opl.to_status, "
            "e.first_name || ' ' || e.last_name AS changed_by_name, "
            "opl.changed_at, opl.duration_minutes "
            "FROM order_process_log opl "
            "LEFT JOIN employees e ON opl.changed_by = e.employee_id "
            "ORDER BY opl.order_id, opl.changed_at " + limit.format(n=50),
        ),
        (
            "Average time from order placed to delivered",
            "SELECT ROUND(AVG(total_min), 1) AS avg_fulfillment_minutes, "
            "ROUND(AVG(total_min) / 60.0, 1) AS avg_fulfillment_hours, "
            "ROUND(AVG(total_min) / 1440.0, 1) AS avg_fulfillment_days "
            "FROM ("
            "  SELECT order_id, SUM(duration_minutes) AS total_min "
            "  FROM order_process_log "
            "  WHERE order_id IN ("
            "    SELECT DISTINCT order_id FROM order_process_log WHERE to_status = 'delivered'"
            "  ) GROUP BY order_id"
            ")",
        ),
    ]


# ---------------------------------------------------------------------------
# SALES PIPELINE
# ---------------------------------------------------------------------------

def _sales_pipeline_docs() -> list[str]:
    return [
        "SALES_PIPELINE tracks sales opportunities (deals) through CRM stages. "
        "Columns: pipeline_id (PK), customer_id (FK to CUSTOMERS), employee_id (FK to EMPLOYEES), "
        "stage (current stage), entered_at (TIMESTAMP), expected_value (deal amount), "
        "probability (0-100), product_interest (text), notes, deal_source. "
        "Pipeline stages in order: lead, qualified, proposal, negotiation, closed_won, closed_lost.",

        "PIPELINE_HISTORY tracks stage transitions for each deal. "
        "Columns: history_id (PK), pipeline_id (FK to SALES_PIPELINE), from_stage, "
        "to_stage, changed_at (TIMESTAMP), changed_by (FK to EMPLOYEES), notes. "
        "Use PIPELINE_HISTORY to calculate time spent in each stage and conversion rates between stages.",

        "The view V_PIPELINE_FUNNEL provides pre-aggregated funnel data: "
        "stage, deal_count, total_value, avg_deal_value, avg_probability.",

        "To calculate sales pipeline conversion rate, count deals at each stage and divide by "
        "total deals. closed_won / total deals = overall win rate. "
        "deal_source values include: Website, Referral, Trade Show, Cold Call, Partner, Inbound Marketing.",
    ]


def _sales_pipeline_examples(limit: str) -> list[tuple[str, str]]:
    return [
        (
            "What is the conversion rate in the sales pipeline?",
            "SELECT stage, COUNT(*) AS deal_count, "
            "ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct_of_total "
            "FROM sales_pipeline "
            "GROUP BY stage "
            "ORDER BY CASE stage "
            "WHEN 'lead' THEN 1 WHEN 'qualified' THEN 2 WHEN 'proposal' THEN 3 "
            "WHEN 'negotiation' THEN 4 WHEN 'closed_won' THEN 5 WHEN 'closed_lost' THEN 6 END",
        ),
        (
            "Show total pipeline value by stage",
            "SELECT stage, "
            "COUNT(*) AS deals, "
            "ROUND(SUM(expected_value), 2) AS total_value, "
            "ROUND(AVG(expected_value), 2) AS avg_deal_value "
            "FROM sales_pipeline "
            "GROUP BY stage "
            "ORDER BY total_value DESC",
        ),
        (
            "Which sales reps have the highest win rate?",
            "SELECT e.first_name || ' ' || e.last_name AS sales_rep, "
            "COUNT(*) AS total_deals, "
            "SUM(CASE WHEN sp.stage = 'closed_won' THEN 1 ELSE 0 END) AS won, "
            "ROUND(SUM(CASE WHEN sp.stage = 'closed_won' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS win_rate_pct "
            "FROM sales_pipeline sp "
            "JOIN employees e ON sp.employee_id = e.employee_id "
            "GROUP BY e.first_name, e.last_name "
            "ORDER BY win_rate_pct DESC",
        ),
        (
            "Show pipeline deals by source",
            "SELECT deal_source, "
            "COUNT(*) AS deals, "
            "ROUND(SUM(expected_value), 2) AS total_value, "
            "SUM(CASE WHEN stage = 'closed_won' THEN 1 ELSE 0 END) AS won_deals "
            "FROM sales_pipeline "
            "GROUP BY deal_source "
            "ORDER BY total_value DESC",
        ),
        (
            "Average time to close a won deal",
            "SELECT ROUND(AVG(closed.closed_at - opened.first_ts), 1) AS avg_days_to_close "
            "FROM ("
            "  SELECT pipeline_id, MIN(changed_at) AS first_ts "
            "  FROM pipeline_history GROUP BY pipeline_id"
            ") opened "
            "JOIN ("
            "  SELECT pipeline_id, MAX(changed_at) AS closed_at "
            "  FROM pipeline_history WHERE to_stage = 'closed_won' GROUP BY pipeline_id"
            ") closed ON opened.pipeline_id = closed.pipeline_id",
        ),
        (
            "Show top 10 highest value deals in pipeline",
            "SELECT sp.pipeline_id, "
            "c.company_name AS customer, "
            "e.first_name || ' ' || e.last_name AS sales_rep, "
            "sp.stage, sp.expected_value, sp.probability, sp.product_interest "
            "FROM sales_pipeline sp "
            "JOIN customers c ON sp.customer_id = c.customer_id "
            "JOIN employees e ON sp.employee_id = e.employee_id "
            "ORDER BY sp.expected_value DESC " + limit.format(n=10),
        ),
    ]


# ---------------------------------------------------------------------------
# SUPPORT TICKETS
# ---------------------------------------------------------------------------

def _support_ticket_docs() -> list[str]:
    return [
        "SUPPORT_TICKETS tracks customer support requests. "
        "Columns: ticket_id (PK), customer_id (FK to CUSTOMERS), assigned_to (FK to EMPLOYEES), "
        "priority (P1/P2/P3/P4 where P1 is most urgent), category, subject, "
        "status (new/assigned/investigating/waiting_customer/in_progress/resolved/closed/reopened), "
        "created_at (TIMESTAMP), updated_at, resolved_at, resolution_minutes (time to resolve).",

        "TICKET_HISTORY tracks status transitions for each ticket. "
        "Columns: history_id (PK), ticket_id (FK to SUPPORT_TICKETS), from_status, "
        "to_status, changed_by (FK to EMPLOYEES), changed_at (TIMESTAMP), notes. "
        "Use TICKET_HISTORY to analyze average time in each status and find workflow bottlenecks.",

        "The view V_TICKET_SLA_ANALYSIS provides SLA metrics by priority and status: "
        "priority, status, ticket_count, avg_resolution_min, avg_resolution_hours. "
        "The view V_SUPPORT_WORKLOAD shows per-engineer workload: "
        "engineer_name, title, total_tickets, open_tickets, resolved_tickets, avg_resolution_min.",

        "Support ticket categories include: Login Issue, Performance, Data Error, Integration, "
        "Billing, Feature Request, Bug Report, Configuration, Access Control, Documentation.",
    ]


def _support_ticket_examples(limit: str) -> list[tuple[str, str]]:
    return [
        (
            "Show average resolution time by priority",
            "SELECT priority, "
            "COUNT(*) AS ticket_count, "
            "ROUND(AVG(resolution_minutes), 0) AS avg_resolution_min, "
            "ROUND(AVG(resolution_minutes) / 60.0, 1) AS avg_resolution_hours "
            "FROM support_tickets "
            "WHERE resolution_minutes IS NOT NULL "
            "GROUP BY priority "
            "ORDER BY priority",
        ),
        (
            "How many tickets are open vs resolved?",
            "SELECT status, COUNT(*) AS ticket_count "
            "FROM support_tickets "
            "GROUP BY status "
            "ORDER BY ticket_count DESC",
        ),
        (
            "Which support engineers have the most tickets?",
            "SELECT e.first_name || ' ' || e.last_name AS engineer, "
            "COUNT(*) AS total_tickets, "
            "SUM(CASE WHEN t.status IN ('resolved','closed') THEN 1 ELSE 0 END) AS resolved, "
            "ROUND(AVG(t.resolution_minutes), 0) AS avg_resolution_min "
            "FROM support_tickets t "
            "JOIN employees e ON t.assigned_to = e.employee_id "
            "GROUP BY e.first_name, e.last_name "
            "ORDER BY total_tickets DESC",
        ),
        (
            "Show ticket count by category and priority",
            "SELECT category, priority, COUNT(*) AS ticket_count "
            "FROM support_tickets "
            "GROUP BY category, priority "
            "ORDER BY category, priority",
        ),
        (
            "Show P1 tickets that are still open",
            "SELECT t.ticket_id, c.company_name AS customer, "
            "t.subject, t.status, t.created_at, "
            "e.first_name || ' ' || e.last_name AS assigned_to_name "
            "FROM support_tickets t "
            "JOIN customers c ON t.customer_id = c.customer_id "
            "LEFT JOIN employees e ON t.assigned_to = e.employee_id "
            "WHERE t.priority = 'P1' "
            "AND t.status NOT IN ('resolved', 'closed') "
            "ORDER BY t.created_at",
        ),
        (
            "What is the average time from ticket creation to resolution by category?",
            "SELECT category, "
            "COUNT(*) AS resolved_tickets, "
            "ROUND(AVG(resolution_minutes), 0) AS avg_min, "
            "ROUND(AVG(resolution_minutes) / 60.0, 1) AS avg_hours "
            "FROM support_tickets "
            "WHERE resolution_minutes IS NOT NULL "
            "GROUP BY category "
            "ORDER BY avg_min DESC",
        ),
        (
            "Show ticket reopening rate",
            "SELECT "
            "COUNT(*) AS total_tickets, "
            "SUM(CASE WHEN status = 'reopened' THEN 1 ELSE 0 END) AS reopened, "
            "ROUND(SUM(CASE WHEN status = 'reopened' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS reopen_rate_pct "
            "FROM support_tickets",
        ),
    ]


# ---------------------------------------------------------------------------
# APPROVAL REQUESTS
# ---------------------------------------------------------------------------

def _approval_docs() -> list[str]:
    return [
        "APPROVAL_REQUESTS tracks multi-level approval workflows for business requests. "
        "Columns: request_id (PK), requester_id (FK to EMPLOYEES), "
        "request_type (purchase/travel/hiring/budget/expense), "
        "description (text), amount (monetary value), "
        "current_step (draft/submitted/level1_review/level2_review/approved/rejected/executed), "
        "status (active/completed/rejected/cancelled), "
        "created_at (TIMESTAMP), updated_at, completed_at.",

        "APPROVAL_STEPS records each step in the approval chain. "
        "Columns: step_id (PK), request_id (FK to APPROVAL_REQUESTS), step_name, "
        "approver_id (FK to EMPLOYEES), action (approve/reject/return/pending), "
        "acted_at (TIMESTAMP), comments. "
        "High-value requests (>$20,000) require level2 approval. "
        "Low-value requests (<$5,000) only need level1 approval.",

        "The view V_APPROVAL_EFFICIENCY provides aggregated metrics: "
        "request_type, current_step, status, request_count, avg_amount, total_amount.",
    ]


def _approval_examples(limit: str) -> list[tuple[str, str]]:
    return [
        (
            "Show approval request summary by type and status",
            "SELECT request_type, status, "
            "COUNT(*) AS request_count, "
            "ROUND(AVG(amount), 2) AS avg_amount, "
            "ROUND(SUM(amount), 2) AS total_amount "
            "FROM approval_requests "
            "GROUP BY request_type, status "
            "ORDER BY request_type, status",
        ),
        (
            "What is the approval rate by request type?",
            "SELECT request_type, "
            "COUNT(*) AS total, "
            "SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS approved, "
            "SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected, "
            "ROUND(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS approval_rate_pct "
            "FROM approval_requests "
            "GROUP BY request_type "
            "ORDER BY approval_rate_pct DESC",
        ),
        (
            "Show pending approval requests",
            "SELECT ar.request_id, "
            "e.first_name || ' ' || e.last_name AS requester, "
            "ar.request_type, ar.amount, ar.current_step, ar.created_at "
            "FROM approval_requests ar "
            "JOIN employees e ON ar.requester_id = e.employee_id "
            "WHERE ar.status = 'active' "
            "ORDER BY ar.created_at " + limit.format(n=20),
        ),
        (
            "Average time to complete approval by request type",
            "SELECT request_type, "
            "COUNT(*) AS completed_count, "
            "ROUND(AVG(CAST(completed_at AS DATE) - CAST(created_at AS DATE)), 1) AS avg_days "
            "FROM approval_requests "
            "WHERE completed_at IS NOT NULL "
            "GROUP BY request_type "
            "ORDER BY avg_days DESC",
        ),
        (
            "Who are the most active approvers?",
            "SELECT e.first_name || ' ' || e.last_name AS approver, "
            "COUNT(*) AS total_actions, "
            "SUM(CASE WHEN astp.action = 'approve' THEN 1 ELSE 0 END) AS approvals, "
            "SUM(CASE WHEN astp.action = 'reject' THEN 1 ELSE 0 END) AS rejections "
            "FROM approval_steps astp "
            "JOIN employees e ON astp.approver_id = e.employee_id "
            "WHERE astp.action IN ('approve', 'reject') "
            "GROUP BY e.first_name, e.last_name "
            "ORDER BY total_actions DESC",
        ),
        (
            "Show high-value requests over 50000",
            "SELECT ar.request_id, "
            "e.first_name || ' ' || e.last_name AS requester, "
            "ar.request_type, ar.amount, ar.current_step, ar.status "
            "FROM approval_requests ar "
            "JOIN employees e ON ar.requester_id = e.employee_id "
            "WHERE ar.amount > 50000 "
            "ORDER BY ar.amount DESC " + limit.format(n=20),
        ),
    ]
