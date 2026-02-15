"""Auto-profiling engine for database tables and columns."""

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from biai.db.base import DatabaseConnector
from biai.models.schema import TableInfo
from biai.models.profile import (
    SemanticType, ColumnStats, ColumnProfile, TableProfile, Anomaly,
)
from biai.utils.logger import get_logger

logger = get_logger(__name__)

_BIAI_DIR = Path.home() / ".biai"

# Patterns for semantic type detection (column name based)
_NAME_PATTERNS: dict[SemanticType, list[str]] = {
    SemanticType.ID: [r"(?:^|_)id$", r"_id$", r"^id_", r"^pk$", r"^key$"],
    SemanticType.EMAIL: [r"e?mail", r"email_address"],
    SemanticType.PHONE: [r"phone", r"tel(?:ephone)?", r"mobile", r"fax"],
    SemanticType.NAME: [r"(?:first|last|full|user|customer|employee)_?name", r"^name$", r"^title$"],
    SemanticType.ADDRESS: [r"address", r"street", r"city", r"state", r"zip", r"postal", r"country"],
    SemanticType.CURRENCY: [r"price", r"cost", r"amount", r"total", r"revenue", r"salary", r"fee", r"balance", r"ltv"],
    SemanticType.PERCENTAGE: [r"percent", r"pct", r"rate", r"ratio"],
    SemanticType.DATE: [r"date$", r"_date$", r"^date_", r"_at$", r"created", r"updated", r"born"],
    SemanticType.DATETIME: [r"timestamp", r"datetime", r"_ts$"],
    SemanticType.STATUS: [r"status", r"state", r"stage", r"phase", r"step"],
    SemanticType.BOOLEAN: [r"^is_", r"^has_", r"^can_", r"^flag", r"active", r"enabled", r"deleted"],
    SemanticType.QUANTITY: [r"count", r"qty", r"quantity", r"number", r"num_", r"total_"],
    SemanticType.URL: [r"url", r"link", r"href", r"website"],
    SemanticType.CODE: [r"code", r"sku", r"isbn", r"ean", r"upc"],
    SemanticType.CATEGORY: [r"type", r"category", r"group", r"class", r"kind", r"level", r"tier"],
}

# Value-based patterns for refinement
_VALUE_PATTERNS: dict[SemanticType, re.Pattern] = {
    SemanticType.EMAIL: re.compile(r"^[^@\s]+@[^@\s]+\.\w+$"),
    SemanticType.PHONE: re.compile(r"^[\+\d\s\-\(\)]{7,20}$"),
    SemanticType.URL: re.compile(r"^https?://\S+$"),
}

# Top-N values to return in profile
_TOP_N = 10
_SAMPLE_ROWS = 5
_SAMPLE_VALUES = 5
_MAX_PROFILE_QUERY_ROWS = 5000


class DataProfiler:
    """Profiles database tables — statistics, semantic types, anomalies."""

    def __init__(self, connector: DatabaseConnector):
        self._connector = connector

    async def profile_table(self, table: TableInfo) -> TableProfile:
        """Profile an entire table: stats for every column + sample rows."""
        logger.info("profiling_table", table=table.full_name)

        # Fetch sample data (capped)
        try:
            df = await self._connector.execute_query(
                f"SELECT * FROM {table.full_name} FETCH FIRST {_MAX_PROFILE_QUERY_ROWS} ROWS ONLY",
                timeout=15,
            )
        except Exception:
            try:
                df = await self._connector.execute_query(
                    f"SELECT * FROM {table.full_name} LIMIT {_MAX_PROFILE_QUERY_ROWS}",
                    timeout=15,
                )
            except Exception as e:
                logger.warning("profile_table_query_failed", table=table.full_name, error=str(e))
                return TableProfile(
                    table_name=table.name,
                    schema_name=table.schema_name,
                    profiled_at=datetime.now(timezone.utc).isoformat(),
                )

        # Get actual row count
        row_count = len(df)
        try:
            count_df = await self._connector.execute_query(
                f"SELECT COUNT(*) AS cnt FROM {table.full_name}", timeout=10,
            )
            if not count_df.empty:
                row_count = int(count_df.iloc[0, 0])
        except Exception:
            pass

        # Profile each column
        column_profiles = []
        for col_info in table.columns:
            if col_info.name in df.columns:
                profile = self._profile_column(
                    col_info.name, col_info.data_type, df[col_info.name], row_count,
                )
            else:
                profile = ColumnProfile(
                    column_name=col_info.name,
                    data_type=col_info.data_type,
                )
            column_profiles.append(profile)

        # Sample rows
        sample_rows = []
        if not df.empty:
            for _, row in df.head(_SAMPLE_ROWS).iterrows():
                sample_rows.append({k: str(v) for k, v in row.items()})

        return TableProfile(
            table_name=table.name,
            schema_name=table.schema_name,
            row_count=row_count,
            column_profiles=column_profiles,
            sample_rows=sample_rows,
            profiled_at=datetime.now(timezone.utc).isoformat(),
        )

    def _profile_column(
        self, col_name: str, data_type: str, series: pd.Series, total_rows: int,
    ) -> ColumnProfile:
        """Profile a single column from a pandas Series."""
        stats = self._compute_statistics(series, total_rows)
        semantic_type = self._detect_semantic_type(col_name, data_type, series)
        anomalies = self._detect_anomalies(series, stats, semantic_type)

        sample_vals = [str(v) for v in series.dropna().head(_SAMPLE_VALUES).tolist()]

        return ColumnProfile(
            column_name=col_name,
            data_type=data_type,
            semantic_type=semantic_type,
            stats=stats,
            anomalies=anomalies,
            sample_values=sample_vals,
        )

    @staticmethod
    def _compute_statistics(series: pd.Series, total_rows: int) -> ColumnStats:
        """Compute basic statistics for a column."""
        null_count = int(series.isna().sum())
        non_null = series.dropna()
        distinct_count = int(non_null.nunique())

        stats = ColumnStats(
            null_count=null_count,
            null_pct=round(null_count / total_rows * 100, 1) if total_rows > 0 else 0.0,
            distinct_count=distinct_count,
            distinct_pct=round(distinct_count / total_rows * 100, 1) if total_rows > 0 else 0.0,
        )

        # Numeric stats
        numeric = pd.to_numeric(non_null, errors="coerce").dropna()
        if len(numeric) > 0:
            stats.min_value = str(numeric.min())
            stats.max_value = str(numeric.max())
            stats.mean = round(float(numeric.mean()), 2)
            stats.median = round(float(numeric.median()), 2)
            if len(numeric) > 1:
                stats.std = round(float(numeric.std()), 2)
        else:
            # String min/max (guard against mixed types)
            try:
                str_vals = non_null.astype(str)
                if len(str_vals) > 0:
                    stats.min_value = str(str_vals.min())
                    stats.max_value = str(str_vals.max())
            except TypeError:
                pass

        # Top values (value counts)
        if len(non_null) > 0:
            vc = non_null.value_counts().head(_TOP_N)
            stats.top_values = [
                {"value": str(val), "count": int(cnt)}
                for val, cnt in vc.items()
            ]

        return stats

    @staticmethod
    def _detect_semantic_type(
        col_name: str, data_type: str, series: pd.Series,
    ) -> SemanticType:
        """Detect semantic type from column name + data type + sample values."""
        name_lower = col_name.lower()
        dtype_lower = data_type.lower()

        # Date/datetime from DB type
        if any(t in dtype_lower for t in ("date", "timestamp", "time")):
            if "timestamp" in dtype_lower or "datetime" in dtype_lower:
                return SemanticType.DATETIME
            return SemanticType.DATE

        # Boolean from DB type
        if "bool" in dtype_lower or "bit" in dtype_lower:
            return SemanticType.BOOLEAN

        # Name-pattern matching
        for sem_type, patterns in _NAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    return sem_type

        # Value-based detection (for strings)
        non_null = series.dropna()
        if len(non_null) > 0 and non_null.dtype == object:
            sample = non_null.head(20).astype(str)
            for sem_type, regex in _VALUE_PATTERNS.items():
                matches = sample.str.match(regex).sum()
                if matches / len(sample) > 0.7:
                    return sem_type

        # Numeric fallback
        numeric = pd.to_numeric(non_null, errors="coerce").dropna()
        if len(numeric) > 0 and len(numeric) / max(len(non_null), 1) > 0.8:
            return SemanticType.NUMERIC

        # Categorical: low cardinality string
        if non_null.dtype == object and 0 < int(non_null.nunique()) <= 30:
            return SemanticType.CATEGORY

        return SemanticType.TEXT if non_null.dtype == object else SemanticType.UNKNOWN

    # --- Batch profiling ---

    async def profile_tables_batch(
        self,
        tables: list[TableInfo],
        concurrency: int = 10,
        on_progress: Callable[[int, int], None] | None = None,
        timeout: float = 60.0,
    ) -> dict[str, TableProfile]:
        """Profile multiple tables in parallel with controlled concurrency.

        Args:
            tables: Tables to profile.
            concurrency: Max concurrent profiling tasks.
            on_progress: Callback(completed, total) for progress updates.
            timeout: Max total time in seconds.

        Returns:
            Dict of table_name -> TableProfile.
        """
        sem = asyncio.Semaphore(concurrency)
        results: dict[str, TableProfile] = {}
        completed = 0
        total = len(tables)

        async def _profile_one(table: TableInfo) -> None:
            nonlocal completed
            async with sem:
                try:
                    profile = await self.profile_table(table)
                    results[table.name] = profile
                except Exception as e:
                    logger.warning(
                        "batch_profile_failed",
                        table=table.name, error=str(e),
                    )
                finally:
                    completed += 1
                    if on_progress:
                        on_progress(completed, total)

        tasks = [_profile_one(t) for t in tables]
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "batch_profile_timeout",
                completed=completed, total=total,
                timeout=timeout,
            )

        logger.info(
            "batch_profile_complete",
            profiled=len(results), total=total,
        )
        return results

    # --- Disk caching ---

    @staticmethod
    def save_cache(profiles: dict[str, TableProfile], db_name: str) -> None:
        """Save profiles to ~/.biai/profiles_{db_name}.json."""
        _BIAI_DIR.mkdir(parents=True, exist_ok=True)
        path = _BIAI_DIR / f"profiles_{db_name}.json"
        data = {
            tname: tp.model_dump() for tname, tp in profiles.items()
        }
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("profiles_cached", path=str(path), tables=len(data))

    @staticmethod
    def load_cache(db_name: str) -> dict[str, TableProfile] | None:
        """Load cached profiles if available."""
        path = _BIAI_DIR / f"profiles_{db_name}.json"
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return {
                tname: TableProfile.model_validate(tdata)
                for tname, tdata in raw.items()
            }
        except Exception as e:
            logger.warning("profiles_cache_load_failed", error=str(e))
            return None

    @staticmethod
    def _detect_anomalies(
        series: pd.Series, stats: ColumnStats, semantic_type: SemanticType,
    ) -> list[Anomaly]:
        """Detect basic anomalies in column data."""
        anomalies = []

        # High null percentage
        if stats.null_pct > 50:
            anomalies.append(Anomaly(
                type="null_spike",
                description=f"{stats.null_pct}% null values",
                severity="medium" if stats.null_pct < 80 else "high",
            ))

        # Numeric outliers (IQR method)
        numeric = pd.to_numeric(series.dropna(), errors="coerce").dropna()
        if len(numeric) > 10:
            q1 = numeric.quantile(0.25)
            q3 = numeric.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outlier_count = int(((numeric < lower) | (numeric > upper)).sum())
                if outlier_count > 0:
                    pct = round(outlier_count / len(numeric) * 100, 1)
                    anomalies.append(Anomaly(
                        type="outlier",
                        description=f"{outlier_count} outliers ({pct}%) outside IQR range [{lower:.1f}, {upper:.1f}]",
                        severity="low" if pct < 5 else "medium",
                    ))

        # Single-value dominance
        if stats.top_values and stats.distinct_count > 1:
            top_pct = stats.top_values[0]["count"] / max(len(series), 1) * 100
            if top_pct > 90:
                anomalies.append(Anomaly(
                    type="suspicious_pattern",
                    description=f"Value '{stats.top_values[0]['value']}' dominates ({top_pct:.0f}%)",
                    severity="low",
                ))

        return anomalies
