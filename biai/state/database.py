"""Database connection state."""

import reflex as rx

from biai.config.constants import DEFAULT_DB_HOST, DEFAULT_POSTGRESQL_PORT, DEFAULT_ORACLE_PORT
from biai.models.connection import DBType, ConnectionConfig


class DBState(rx.State):
    """Manages database connection state."""

    # Connection form fields
    db_type: str = "postgresql"
    host: str = DEFAULT_DB_HOST
    port: int = DEFAULT_POSTGRESQL_PORT
    database: str = ""
    username: str = ""
    password: str = ""
    dsn: str = ""

    # Connection status
    is_connected: bool = False
    is_connecting: bool = False
    server_version: str = ""
    connection_error: str = ""
    is_read_only: bool = True

    # Connector reference (not serialized)
    _connector: any = None

    def set_db_type(self, value: str):
        if value == self.db_type:
            return
        self.db_type = value
        self.connection_error = ""
        if value == "oracle":
            self.port = DEFAULT_ORACLE_PORT
        else:
            self.port = DEFAULT_POSTGRESQL_PORT

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

    @rx.var
    def can_connect(self) -> bool:
        """Check if minimum required fields are filled for connection."""
        if self.dsn:
            return bool(self.username)
        return bool(self.host and self.database and self.username)

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

            if success:
                await connector.connect()

            # Check write permissions (non-blocking)
            read_only = True
            if success:
                read_only = await self._check_read_only(connector)

            async with self:
                if success:
                    self.is_connected = True
                    self.server_version = message
                    self.connection_error = ""
                    self._connector = connector
                    self.is_read_only = read_only
                else:
                    self.is_connected = False
                    self.connection_error = self._friendly_error(message)
                    self._connector = None

            # Auto-refresh schema after successful connect
            if success:
                try:
                    from biai.db.schema_manager import SchemaManager
                    from biai.state.schema import SchemaState

                    manager = SchemaManager(connector)
                    snapshot = await manager.get_snapshot(force_refresh=True)

                    async with self:
                        schema_state = await self.get_state(SchemaState)
                    tables_flat: list[dict[str, str]] = []
                    tables_full: list[dict] = []
                    for table in snapshot.tables:
                        cols = []
                        for c in table.columns:
                            cols.append({
                                "name": c.name,
                                "data_type": c.data_type,
                                "is_pk": c.is_primary_key,
                                "is_fk": c.is_foreign_key,
                                "fk_ref": c.foreign_key_ref or "",
                            })
                        tables_flat.append({
                            "name": table.name,
                            "schema": table.schema_name,
                            "col_count": str(len(cols)),
                        })
                        tables_full.append({"name": table.name, "columns": cols})

                    async with schema_state:
                        schema_state.tables = tables_flat
                        schema_state._tables_full = tables_full
                        schema_state.schema_error = ""
                        schema_state._compute_erd()
                except Exception:
                    pass  # Schema refresh is non-blocking
        except Exception as e:
            async with self:
                self.is_connected = False
                self.connection_error = self._friendly_error(str(e))
                self._connector = None
        finally:
            async with self:
                self.is_connecting = False

    @staticmethod
    def _friendly_error(raw: str) -> str:
        """Convert raw DB errors to user-friendly messages."""
        low = raw.lower()
        if "password authentication failed" in low or "autoryzacja haslem" in low:
            return "Authentication failed. Check your username and password."
        if "could not connect to server" in low or "connection refused" in low:
            return "Cannot connect to the database server. Check host and port."
        if "does not exist" in low and "database" in low:
            return "Database not found. Check the database name."
        if "bequeath" in low or "thick mode" in low:
            return "Oracle connection requires thick mode driver. Install Oracle Instant Client."
        if "timeout" in low or "timed out" in low:
            return "Connection timed out. Check if the database server is running."
        if "name or service not known" in low or "could not translate host" in low:
            return "Cannot resolve hostname. Check the host address."
        return raw

    @staticmethod
    async def _check_read_only(connector) -> bool:
        """Check if DB user is read-only by attempting to create a temp table.

        Returns True if read-only, False if user has write permissions.
        """
        import asyncio

        try:
            from biai.db.postgresql import PostgreSQLConnector
            if isinstance(connector, PostgreSQLConnector) and connector._pool:
                async with connector._pool.acquire() as conn:
                    await conn.execute("CREATE TEMP TABLE _biai_rw_check (id int)")
                    await conn.execute("DROP TABLE IF EXISTS _biai_rw_check")
                return False  # Has write permissions

            from biai.db.oracle import OracleConnector
            if isinstance(connector, OracleConnector) and connector._pool:
                def _oracle_check():
                    conn = connector._pool.acquire()
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            "CREATE GLOBAL TEMPORARY TABLE biai_rw_check "
                            "(id NUMBER) ON COMMIT PRESERVE ROWS"
                        )
                        cursor.execute("DROP TABLE biai_rw_check")
                        cursor.close()
                    finally:
                        connector._pool.release(conn)

                await asyncio.to_thread(_oracle_check)
                return False  # Has write permissions

            return True  # Unknown connector type, assume read-only
        except Exception:
            return True  # Error = read-only (no write permissions)

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
            self.is_read_only = True

        # Reset schema training flag so next connect retrains
        try:
            from biai.state.chat import ChatState
            async with self:
                chat_state = await self.get_state(ChatState)
            async with chat_state:
                chat_state._schema_trained = False
        except Exception:
            pass

        # Clear schema only; keep dashboard data (query results + chart) visible
        # so the user can still see previous results after disconnect.
        try:
            from biai.state.schema import SchemaState
            async with self:
                schema_state = await self.get_state(SchemaState)
            async with schema_state:
                schema_state.tables = []
                schema_state._tables_full = []
                schema_state.selected_table = ""
                schema_state.selected_columns = []
                schema_state.search_query = ""
                schema_state.schema_error = ""
        except Exception:
            pass

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
                    self.connection_error = self._friendly_error(message)
        except Exception as e:
            async with self:
                self.connection_error = self._friendly_error(str(e))
        finally:
            async with self:
                self.is_connecting = False
