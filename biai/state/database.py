"""Database connection state."""

import asyncio
import reflex as rx

from biai.models.connection import DBType, ConnectionConfig


class DBState(rx.State):
    """Manages database connection state."""

    # Connection form fields
    db_type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    dsn: str = ""

    # Connection status
    is_connected: bool = False
    is_connecting: bool = False
    server_version: str = ""
    connection_error: str = ""

    # Connector reference (not serialized)
    _connector: any = None

    def set_db_type(self, value: str):
        self.db_type = value
        if value == "oracle":
            self.port = 1521
        else:
            self.port = 5432

    def set_host(self, value: str):
        self.host = value

    def set_port(self, value: str):
        try:
            self.port = int(value)
        except ValueError:
            pass

    def set_database(self, value: str):
        self.database = value

    def set_username(self, value: str):
        self.username = value

    def set_password(self, value: str):
        self.password = value

    def set_dsn(self, value: str):
        self.dsn = value

    def _get_config(self) -> ConnectionConfig:
        return ConnectionConfig(
            db_type=DBType(self.db_type),
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            password=self.password,
            dsn=self.dsn,
        )

    @rx.event(background=True)
    async def connect(self):
        async with self:
            self.is_connecting = True
            self.connection_error = ""

        try:
            config = None
            async with self:
                config = self._get_config()

            if config.db_type == DBType.ORACLE:
                from biai.db.oracle import OracleConnector
                connector = OracleConnector(config)
            else:
                from biai.db.postgresql import PostgreSQLConnector
                connector = PostgreSQLConnector(config)

            success, message = await connector.test_connection()

            async with self:
                if success:
                    self.is_connected = True
                    self.server_version = message
                    self.connection_error = ""
                    self._connector = connector
                else:
                    self.is_connected = False
                    self.connection_error = message
                    self._connector = None
        except Exception as e:
            async with self:
                self.is_connected = False
                self.connection_error = str(e)
                self._connector = None
        finally:
            async with self:
                self.is_connecting = False

    @rx.event(background=True)
    async def disconnect(self):
        async with self:
            if self._connector:
                try:
                    await self._connector.disconnect()
                except Exception:
                    pass
            self._connector = None
            self.is_connected = False
            self.server_version = ""

    @rx.event(background=True)
    async def test_connection(self):
        async with self:
            self.is_connecting = True
            self.connection_error = ""

        try:
            config = None
            async with self:
                config = self._get_config()

            if config.db_type == DBType.ORACLE:
                from biai.db.oracle import OracleConnector
                connector = OracleConnector(config)
            else:
                from biai.db.postgresql import PostgreSQLConnector
                connector = PostgreSQLConnector(config)

            success, message = await connector.test_connection()

            async with self:
                if success:
                    self.connection_error = ""
                    self.server_version = message
                else:
                    self.connection_error = message
        except Exception as e:
            async with self:
                self.connection_error = str(e)
        finally:
            async with self:
                self.is_connecting = False
