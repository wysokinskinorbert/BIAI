"""Application constants."""

# AI Pipeline
MAX_RETRIES: int = 5
DEFAULT_MODEL: str = "qwen3-coder:30b"
DEFAULT_OLLAMA_HOST: str = "http://localhost:11434"
DEFAULT_CHROMA_HOST: str = "http://localhost:8000"
DEFAULT_CHROMA_COLLECTION: str = "biai_schema"

# Database
QUERY_TIMEOUT: int = 30
ROW_LIMIT: int = 10_000
SCHEMA_CACHE_TTL: int = 300  # 5 minutes
DEFAULT_POSTGRESQL_PORT: int = 5432
DEFAULT_ORACLE_PORT: int = 1521
DEFAULT_DB_HOST: str = "localhost"

# UI
CHAT_PANEL_WIDTH: str = "40%"
DASHBOARD_PANEL_WIDTH: str = "60%"
MAX_CHAT_HISTORY: int = 100
DISPLAY_ROW_LIMIT: int = 100

# SQL Security
BLOCKED_KEYWORDS: list[str] = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "MERGE",
    "CALL",
    "DBMS_",
    "UTL_FILE",
    "UTL_HTTP",
    "xp_cmdshell",
    "sp_execute",
]

# Process Visualization
MAX_PROCESS_NODES: int = 50
PROCESS_DETECTION_ENABLED: bool = True

# Dynamic Process Discovery
USE_DYNAMIC_DISCOVERY: bool = True
DISCOVERY_MAX_TABLES: int = 50
DISCOVERY_MAX_CARDINALITY: int = 30
DISCOVERY_QUERY_TIMEOUT: int = 10
DISCOVERY_CACHE_TTL: int = 600  # 10 minutes

BLOCKED_PATTERNS: list[str] = [
    r";\s*\w",  # multiple statements
    r"--",  # SQL comments (potential injection)
    r"/\*",  # block comments
    r"INTO\s+OUTFILE",
    r"INTO\s+DUMPFILE",
    r"LOAD_FILE",
]

