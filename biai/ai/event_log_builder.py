"""Event log builder — transforms database data into standard event logs.

Three strategies based on discovered process patterns:
1. Transition table (from_status/to_status + timestamp)
2. Status + timestamps (lifecycle reconstruction from single table)
3. FK chain (cross-table join with timestamp ordering)
"""

from datetime import datetime

from biai.db.base import DatabaseConnector
from biai.models.discovery import DiscoveredProcess
from biai.models.event_log import EventLog, EventRecord
from biai.utils.logger import get_logger

logger = get_logger(__name__)

# Safety limits
_MAX_CASES = 1000
_MAX_EVENTS_PER_CASE = 100
_QUERY_TIMEOUT = 15


class EventLogBuilder:
    """Builds event logs from database tables using discovered process patterns."""

    def __init__(self, connector: DatabaseConnector, schema_name: str = ""):
        self._connector = connector
        self._schema_name = schema_name

    def _qualified(self, table_name: str) -> str:
        if self._schema_name:
            return f"{self._schema_name}.{table_name}"
        return table_name

    async def build(self, process: DiscoveredProcess) -> EventLog | None:
        """Auto-select strategy based on process discovery signals.

        Returns EventLog or None if no strategy applies.
        """
        try:
            if process.transition_pattern:
                return await self._from_transition_table(process)
            elif process.status_column and self._has_timestamps(process):
                return await self._from_status_with_timestamps(process)
            elif process.entity_chain and len(process.entity_chain.tables) >= 2:
                return await self._from_fk_chain(process)
        except Exception as e:
            logger.warning(
                "event_log_build_failed",
                process=process.id, error=str(e),
            )
        return None

    def _has_timestamps(self, process: DiscoveredProcess) -> bool:
        """Check if process has timestamp evidence."""
        return any(
            e.signal_type == "timestamp_sequence"
            for e in process.evidence
        )

    # ------------------------------------------------------------------
    # Strategy 1: Transition table
    # ------------------------------------------------------------------

    async def _from_transition_table(self, process: DiscoveredProcess) -> EventLog | None:
        """Build event log from a table with from_status/to_status columns."""
        tp = process.transition_pattern
        if not tp:
            return None

        table = self._qualified(tp.table_name)

        # Find entity FK column (first FK in the table)
        entity_col = None
        if process.entity_chain and process.entity_chain.join_keys:
            entity_col = process.entity_chain.join_keys[0][0]

        # Build query
        select_cols = [tp.from_column, tp.to_column]
        if tp.timestamp_column:
            select_cols.append(tp.timestamp_column)
        if entity_col:
            select_cols.append(entity_col)

        cols_str = ", ".join(select_cols)
        order_by = tp.timestamp_column if tp.timestamp_column else tp.from_column
        sql = (
            f"SELECT {cols_str} FROM {table} "
            f"WHERE {tp.from_column} IS NOT NULL AND {tp.to_column} IS NOT NULL "
            f"ORDER BY {order_by}"
        )

        df = await self._connector.execute_query(sql, timeout=_QUERY_TIMEOUT)
        if df.empty:
            return None

        # Limit rows
        df = df.head(_MAX_CASES * 2)

        events: list[EventRecord] = []
        for _, row in df.iterrows():
            case_id = str(row[entity_col]) if entity_col and entity_col in df.columns else str(_ + 1)

            ts = None
            if tp.timestamp_column and tp.timestamp_column in df.columns:
                raw_ts = row[tp.timestamp_column]
                ts = _parse_timestamp(raw_ts)

            events.append(EventRecord(
                case_id=case_id,
                activity=str(row[tp.to_column]),
                timestamp=ts,
                entity_type=process.id,
            ))

        return self._build_log(process.id, events)

    # ------------------------------------------------------------------
    # Strategy 2: Status + timestamps
    # ------------------------------------------------------------------

    async def _from_status_with_timestamps(self, process: DiscoveredProcess) -> EventLog | None:
        """Build event log from a table with status column + timestamps."""
        sc = process.status_column
        if not sc:
            return None

        table = self._qualified(sc.table_name)

        # Find PK column for case_id
        pk_col = "ROWID"  # fallback
        for t in getattr(process, '_schema_tables', []):
            if t.name.upper() == sc.table_name.upper():
                for c in t.columns:
                    if c.is_primary_key:
                        pk_col = c.name
                        break
                break

        # Current snapshot: one event per row (status + last update timestamp)
        sql = (
            f"SELECT {pk_col}, {sc.column_name} "
            f"FROM {table} "
            f"WHERE {sc.column_name} IS NOT NULL "
            f"ORDER BY {pk_col}"
        )

        df = await self._connector.execute_query(sql, timeout=_QUERY_TIMEOUT)
        if df.empty:
            return None

        df = df.head(_MAX_CASES)

        events: list[EventRecord] = []
        for _, row in df.iterrows():
            case_id = str(row.iloc[0])
            activity = str(row.iloc[1])
            events.append(EventRecord(
                case_id=case_id,
                activity=activity,
                entity_type=process.id,
            ))

        return self._build_log(process.id, events)

    # ------------------------------------------------------------------
    # Strategy 3: FK chain
    # ------------------------------------------------------------------

    async def _from_fk_chain(self, process: DiscoveredProcess) -> EventLog | None:
        """Build event log from FK chain tables joined by entity key."""
        chain = process.entity_chain
        if not chain or len(chain.tables) < 2:
            return None

        # Simple approach: query root table for entity IDs
        root_table = self._qualified(chain.tables[0])
        sql = f"SELECT * FROM {root_table} ORDER BY 1"

        df = await self._connector.execute_query(sql, timeout=_QUERY_TIMEOUT)
        if df.empty:
            return None

        df = df.head(_MAX_CASES)

        events: list[EventRecord] = []
        for _, row in df.iterrows():
            case_id = str(row.iloc[0])  # PK as case ID
            events.append(EventRecord(
                case_id=case_id,
                activity=f"{chain.tables[0]}.created",
                entity_type=process.id,
            ))

        return self._build_log(process.id, events)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_log(process_id: str, events: list[EventRecord]) -> EventLog:
        """Build EventLog from events list."""
        case_ids = {e.case_id for e in events}
        activities = {e.activity for e in events}
        return EventLog(
            process_id=process_id,
            events=events,
            case_count=len(case_ids),
            activity_count=len(activities),
        )


def _parse_timestamp(raw) -> datetime | None:
    """Parse raw DB value to datetime."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        return datetime.fromisoformat(str(raw))
    except (ValueError, TypeError):
        return None
