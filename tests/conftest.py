"""Test fixtures and mocks."""

import pytest
import pandas as pd

from biai.models.connection import ConnectionConfig, DBType
from biai.models.schema import TableInfo, ColumnInfo, SchemaSnapshot


@pytest.fixture
def sample_oracle_config():
    return ConnectionConfig(
        db_type=DBType.ORACLE,
        host="localhost",
        port=1521,
        database="XEPDB1",
        username="test_user",
        password="test_pass",
    )


@pytest.fixture
def sample_pg_config():
    return ConnectionConfig(
        db_type=DBType.POSTGRESQL,
        host="localhost",
        port=5432,
        database="testdb",
        username="test_user",
        password="test_pass",
    )


@pytest.fixture
def sample_schema():
    return SchemaSnapshot(
        tables=[
            TableInfo(
                name="customers",
                schema_name="public",
                columns=[
                    ColumnInfo(name="id", data_type="integer", nullable=False, is_primary_key=True),
                    ColumnInfo(name="name", data_type="varchar(100)", nullable=False),
                    ColumnInfo(name="email", data_type="varchar(200)", nullable=True),
                    ColumnInfo(name="created_at", data_type="timestamp", nullable=False),
                ],
            ),
            TableInfo(
                name="orders",
                schema_name="public",
                columns=[
                    ColumnInfo(name="id", data_type="integer", nullable=False, is_primary_key=True),
                    ColumnInfo(name="customer_id", data_type="integer", nullable=False,
                               is_foreign_key=True, foreign_key_ref="customers"),
                    ColumnInfo(name="amount", data_type="numeric(10,2)", nullable=False),
                    ColumnInfo(name="order_date", data_type="date", nullable=False),
                    ColumnInfo(name="status", data_type="varchar(20)", nullable=False),
                ],
            ),
        ],
        db_type="postgresql",
        schema_name="public",
    )


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        "customer_name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "total_revenue": [15000.50, 12300.00, 9800.75, 8500.25, 7200.00],
        "order_count": [25, 18, 15, 12, 10],
    })
