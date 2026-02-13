"""Dynamic color and icon assignment for process statuses.

Replaces hardcoded STATUS_COLORS/STATUS_ICONS with an algorithmic approach:
1. AI suggestion (highest priority)
2. Semantic keyword matching
3. Deterministic hash-based fallback
"""

import hashlib


class DynamicStyler:
    """Assigns colors and icons to process statuses dynamically."""

    # WCAG AA compliant palette on dark backgrounds (12 colors)
    PALETTE = [
        "#6366f1",  # indigo
        "#3b82f6",  # blue
        "#0ea5e9",  # sky
        "#06b6d4",  # cyan
        "#14b8a6",  # teal
        "#22c55e",  # green
        "#84cc16",  # lime
        "#eab308",  # yellow
        "#f97316",  # orange
        "#ef4444",  # red
        "#ec4899",  # pink
        "#a855f7",  # purple
    ]

    # Semantic color mappings: category -> (color, list of keywords)
    SEMANTIC_COLORS: dict[str, tuple[str, list[str]]] = {
        "success": (
            "#22c55e",
            [
                "delivered", "completed", "approved", "resolved", "done",
                "won", "closed_won", "executed", "confirmed", "active",
                "payment_confirmed", "success", "finished", "accepted",
            ],
        ),
        "error": (
            "#ef4444",
            [
                "rejected", "cancelled", "failed", "closed_lost", "error",
                "blocked", "denied", "expired", "aborted", "terminated",
            ],
        ),
        "warning": (
            "#eab308",
            [
                "pending", "waiting", "waiting_customer", "payment_pending",
                "on_hold", "paused", "delayed", "overdue", "stalled",
            ],
        ),
        "info": (
            "#3b82f6",
            [
                "in_progress", "in_transit", "investigating", "processing",
                "picking", "packing", "working", "running", "active",
                "assigned", "in_review",
            ],
        ),
        "review": (
            "#a855f7",
            [
                "review", "level1_review", "level2_review", "negotiation",
                "proposal", "evaluation", "assessment", "inspection",
            ],
        ),
        "start": (
            "#6366f1",
            [
                "new", "created", "draft", "lead", "submitted", "opened",
                "initiated", "order_placed", "registered", "qualified",
                "warehouse_assigned",
            ],
        ),
        "neutral": (
            "#6b7280",
            [
                "unknown", "other", "none", "n/a", "default",
            ],
        ),
        "transition": (
            "#0ea5e9",
            [
                "shipped", "transferred", "moved", "migrated", "forwarded",
                "escalated", "dispatched",
            ],
        ),
        "reopen": (
            "#f97316",
            [
                "reopened", "returned", "reverted", "rollback",
                "resubmitted", "retried",
            ],
        ),
    }

    # Semantic icon mappings: keyword -> Lucide icon name
    SEMANTIC_ICONS: dict[str, str] = {
        # Lifecycle
        "new": "plus-circle",
        "created": "plus-circle",
        "draft": "file-edit",
        "submitted": "send",
        "opened": "folder-open",
        "initiated": "play",
        "registered": "clipboard-list",
        # Assignment
        "assigned": "user",
        "qualified": "user-check",
        "lead": "user-plus",
        # Processing
        "in_progress": "loader",
        "processing": "loader",
        "working": "wrench",
        "running": "activity",
        "investigating": "search",
        "picking": "package-search",
        "packing": "package",
        # Review
        "review": "eye",
        "level1_review": "eye",
        "level2_review": "shield-check",
        "evaluation": "clipboard-check",
        "proposal": "file-text",
        "negotiation": "handshake",
        "assessment": "list-checks",
        # Waiting
        "pending": "clock",
        "waiting": "clock",
        "waiting_customer": "clock",
        "payment_pending": "credit-card",
        "on_hold": "pause-circle",
        "paused": "pause-circle",
        # Shipping/Transit
        "shipped": "truck",
        "in_transit": "route",
        "dispatched": "send",
        "transferred": "arrow-right-left",
        "warehouse_assigned": "warehouse",
        # Financial
        "payment_confirmed": "circle-check",
        "order_placed": "shopping-cart",
        # Completion
        "completed": "circle-check-big",
        "delivered": "package-check",
        "resolved": "check",
        "done": "circle-check",
        "approved": "thumbs-up",
        "executed": "circle-play",
        "confirmed": "circle-check",
        "closed": "circle-check-big",
        "closed_won": "trophy",
        "won": "trophy",
        "accepted": "thumbs-up",
        "finished": "flag",
        # Negative
        "rejected": "thumbs-down",
        "cancelled": "x-circle",
        "failed": "x-circle",
        "closed_lost": "x-circle",
        "denied": "ban",
        "blocked": "shield-off",
        "expired": "timer-off",
        # Reopen
        "reopened": "refresh-cw",
        "returned": "undo-2",
        "reverted": "undo",
        "resubmitted": "repeat",
        # Escalation
        "escalated": "arrow-up-circle",
    }

    DEFAULT_COLOR = "#6b7280"
    DEFAULT_ICON = "circle"

    @classmethod
    def get_color(cls, status_id: str, ai_suggestion: str | None = None) -> str:
        """Get color for a status.

        Priority: AI suggestion > exact semantic match > partial semantic match > hash-based.
        """
        if ai_suggestion and ai_suggestion.startswith("#"):
            return ai_suggestion

        status_lower = status_id.lower().strip()

        # Pass 1: Exact match across all categories
        for _category, (color, keywords) in cls.SEMANTIC_COLORS.items():
            if status_lower in keywords:
                return color

        # Pass 2: Partial match (keyword is substring of status)
        for _category, (color, keywords) in cls.SEMANTIC_COLORS.items():
            for kw in keywords:
                if kw in status_lower:
                    return color

        # Hash-based deterministic fallback
        return cls._hash_color(status_lower)

    @classmethod
    def get_icon(cls, status_id: str, ai_suggestion: str | None = None) -> str:
        """Get Lucide icon name for a status.

        Priority: AI suggestion > exact match > longest partial match > default.
        """
        if ai_suggestion and ai_suggestion.strip():
            return ai_suggestion.strip()

        status_lower = status_id.lower().strip()

        # Direct match
        if status_lower in cls.SEMANTIC_ICONS:
            return cls.SEMANTIC_ICONS[status_lower]

        # Partial match: find the longest keyword that's a substring (most specific)
        best_icon = None
        best_len = 0
        for keyword, icon in cls.SEMANTIC_ICONS.items():
            if keyword in status_lower and len(keyword) > best_len:
                best_len = len(keyword)
                best_icon = icon

        if best_icon:
            return best_icon

        return cls.DEFAULT_ICON

    @classmethod
    def _hash_color(cls, status: str) -> str:
        """Deterministic color from hash - same status always gets same color."""
        h = int(hashlib.md5(status.encode()).hexdigest(), 16)
        return cls.PALETTE[h % len(cls.PALETTE)]
