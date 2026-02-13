"""Tests for DataProfiler — semantic type detection, statistics, anomalies, caching."""

import json
from pathlib import Path

import pandas as pd
import pytest

from biai.ai.data_profiler import DataProfiler
from biai.models.profile import (
    SemanticType, ColumnStats, ColumnProfile, TableProfile, Anomaly,
)


class TestSemanticTypeDetection:
    """Test _detect_semantic_type() heuristics."""

    def test_id_column(self):
        series = pd.Series([1, 2, 3, 4, 5])
        result = DataProfiler._detect_semantic_type("customer_id", "integer", series)
        assert result == SemanticType.ID

    def test_email_column_by_name(self):
        series = pd.Series(["a@b.com", "c@d.com"])
        result = DataProfiler._detect_semantic_type("email", "varchar", series)
        assert result == SemanticType.EMAIL

    def test_email_address_column_name(self):
        series = pd.Series(["john@example.com", "jane@test.org"])
        result = DataProfiler._detect_semantic_type("email_address", "varchar", series)
        assert result == SemanticType.EMAIL

    def test_phone_column(self):
        series = pd.Series(["+1-555-1234", "+48 600 123 456"])
        result = DataProfiler._detect_semantic_type("phone", "varchar", series)
        assert result == SemanticType.PHONE

    def test_currency_column(self):
        series = pd.Series([100.50, 200.99, 50.00])
        result = DataProfiler._detect_semantic_type("total_amount", "numeric", series)
        assert result == SemanticType.CURRENCY

    def test_date_from_dbtype(self):
        series = pd.Series(["2024-01-01", "2024-02-01"])
        result = DataProfiler._detect_semantic_type("created", "timestamp", series)
        assert result == SemanticType.DATETIME

    def test_date_column_name(self):
        series = pd.Series(["2024-01-01"])
        result = DataProfiler._detect_semantic_type("order_date", "varchar", series)
        assert result == SemanticType.DATE

    def test_boolean_from_dbtype(self):
        series = pd.Series([True, False, True])
        result = DataProfiler._detect_semantic_type("flag", "boolean", series)
        assert result == SemanticType.BOOLEAN

    def test_boolean_column_name(self):
        series = pd.Series([1, 0, 1])
        result = DataProfiler._detect_semantic_type("is_active", "integer", series)
        assert result == SemanticType.BOOLEAN

    def test_status_column(self):
        series = pd.Series(["active", "inactive", "pending"])
        result = DataProfiler._detect_semantic_type("status", "varchar", series)
        assert result == SemanticType.STATUS

    def test_category_low_cardinality(self):
        series = pd.Series(["A", "B", "C", "A", "B"] * 20)
        result = DataProfiler._detect_semantic_type("region_code", "varchar", series)
        assert result in (SemanticType.CODE, SemanticType.CATEGORY)

    def test_url_column(self):
        series = pd.Series(["https://example.com", "https://test.org"])
        result = DataProfiler._detect_semantic_type("website_url", "varchar", series)
        assert result == SemanticType.URL

    def test_numeric_fallback(self):
        series = pd.Series([1.5, 2.7, 3.9, 4.1, 5.0])
        result = DataProfiler._detect_semantic_type("score", "float", series)
        assert result == SemanticType.NUMERIC

    def test_name_column(self):
        series = pd.Series(["John", "Jane", "Bob"])
        result = DataProfiler._detect_semantic_type("first_name", "varchar", series)
        assert result == SemanticType.NAME

    def test_address_column(self):
        series = pd.Series(["123 Main St", "456 Oak Ave"])
        result = DataProfiler._detect_semantic_type("street_address", "varchar", series)
        assert result == SemanticType.ADDRESS

    def test_quantity_column(self):
        series = pd.Series([10, 20, 5, 100])
        result = DataProfiler._detect_semantic_type("quantity", "integer", series)
        assert result == SemanticType.QUANTITY


class TestComputeStatistics:
    """Test _compute_statistics() calculations."""

    def test_basic_numeric_stats(self):
        series = pd.Series([10, 20, 30, 40, 50])
        stats = DataProfiler._compute_statistics(series, total_rows=5)
        assert stats.null_count == 0
        assert stats.null_pct == 0.0
        assert stats.distinct_count == 5
        assert stats.mean == 30.0
        assert stats.median == 30.0
        assert float(stats.min_value) == 10.0
        assert float(stats.max_value) == 50.0

    def test_with_nulls(self):
        series = pd.Series([1, 2, None, 4, None])
        stats = DataProfiler._compute_statistics(series, total_rows=5)
        assert stats.null_count == 2
        assert stats.null_pct == 40.0
        assert stats.distinct_count == 3

    def test_string_column(self):
        series = pd.Series(["apple", "banana", "cherry", "apple"])
        stats = DataProfiler._compute_statistics(series, total_rows=4)
        assert stats.distinct_count == 3
        assert stats.mean is None
        assert len(stats.top_values) > 0

    def test_top_values(self):
        series = pd.Series(["A", "B", "A", "A", "B", "C"])
        stats = DataProfiler._compute_statistics(series, total_rows=6)
        assert stats.top_values[0]["value"] == "A"
        assert stats.top_values[0]["count"] == 3

    def test_all_nulls(self):
        series = pd.Series([None, None, None])
        stats = DataProfiler._compute_statistics(series, total_rows=3)
        assert stats.null_count == 3
        assert stats.null_pct == 100.0
        assert stats.distinct_count == 0

    def test_empty_series(self):
        series = pd.Series([], dtype=float)
        stats = DataProfiler._compute_statistics(series, total_rows=0)
        assert stats.null_count == 0
        assert stats.distinct_count == 0

    def test_std_computed(self):
        series = pd.Series([10, 20, 30, 40, 50])
        stats = DataProfiler._compute_statistics(series, total_rows=5)
        assert stats.std is not None
        assert stats.std > 0


class TestDetectAnomalies:
    """Test _detect_anomalies() detection."""

    def test_high_null_spike(self):
        series = pd.Series([1, None, None, None, None, None])
        stats = ColumnStats(null_count=5, null_pct=83.3)
        anomalies = DataProfiler._detect_anomalies(series, stats, SemanticType.NUMERIC)
        types = [a.type for a in anomalies]
        assert "null_spike" in types

    def test_no_anomaly_normal_data(self):
        series = pd.Series(list(range(100)))
        stats = DataProfiler._compute_statistics(series, total_rows=100)
        anomalies = DataProfiler._detect_anomalies(series, stats, SemanticType.NUMERIC)
        # Normal sequential data should have few/no anomalies
        assert len(anomalies) <= 1

    def test_outlier_detection(self):
        # Create data with clear outliers — need >10 distinct values for IQR
        values = list(range(1, 51)) + [10000]
        normal = pd.Series(values)
        stats = DataProfiler._compute_statistics(normal, total_rows=len(values))
        anomalies = DataProfiler._detect_anomalies(normal, stats, SemanticType.NUMERIC)
        types = [a.type for a in anomalies]
        assert "outlier" in types

    def test_single_value_dominance(self):
        series = pd.Series(["A"] * 95 + ["B"] * 5)
        stats = DataProfiler._compute_statistics(series, total_rows=100)
        anomalies = DataProfiler._detect_anomalies(series, stats, SemanticType.CATEGORY)
        types = [a.type for a in anomalies]
        assert "suspicious_pattern" in types

    def test_no_null_spike_below_threshold(self):
        series = pd.Series([1, 2, None])
        stats = ColumnStats(null_count=1, null_pct=33.3)
        anomalies = DataProfiler._detect_anomalies(series, stats, SemanticType.NUMERIC)
        types = [a.type for a in anomalies]
        assert "null_spike" not in types


class TestProfileCaching:
    """Test save/load cache for profiles."""

    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("biai.ai.data_profiler._BIAI_DIR", tmp_path)

        profiles = {
            "customers": TableProfile(
                table_name="customers",
                schema_name="public",
                row_count=100,
                column_profiles=[
                    ColumnProfile(
                        column_name="id",
                        data_type="integer",
                        semantic_type=SemanticType.ID,
                    ),
                    ColumnProfile(
                        column_name="email",
                        data_type="varchar",
                        semantic_type=SemanticType.EMAIL,
                    ),
                ],
            ),
        }

        DataProfiler.save_cache(profiles, "test_db")

        # Verify file created
        cache_path = tmp_path / "profiles_test_db.json"
        assert cache_path.exists()

        # Load back
        loaded = DataProfiler.load_cache("test_db")
        assert loaded is not None
        assert "customers" in loaded
        assert loaded["customers"].table_name == "customers"
        assert loaded["customers"].row_count == 100
        assert len(loaded["customers"].column_profiles) == 2
        assert loaded["customers"].column_profiles[0].semantic_type == SemanticType.ID

    def test_load_missing_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("biai.ai.data_profiler._BIAI_DIR", tmp_path)
        result = DataProfiler.load_cache("nonexistent")
        assert result is None

    def test_load_corrupted_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("biai.ai.data_profiler._BIAI_DIR", tmp_path)
        path = tmp_path / "profiles_bad.json"
        path.write_text("not valid json{{{", encoding="utf-8")
        result = DataProfiler.load_cache("bad")
        assert result is None
