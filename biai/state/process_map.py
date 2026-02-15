"""Process map state - shows discovered processes as interactive cards."""

import reflex as rx
from pydantic import BaseModel, Field

from biai.utils.logger import get_logger

logger = get_logger(__name__)


class EvidenceInfo(BaseModel):
    """Serializable evidence item for UI display."""
    signal_type: str = ""
    description: str = ""
    strength: float = 0.0


class ProcessInfo(BaseModel):
    """Serializable process info for rx.foreach rendering."""
    id: str = ""
    name: str = ""
    description: str = ""
    stages: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: list[EvidenceInfo] = Field(default_factory=list)
    domain: str = ""


class ProcessMapState(rx.State):
    """Manages discovery and display of process map cards."""

    # Serialized DiscoveredProcess list (rx.Base subclass for rx.foreach compat)
    discovered_processes: list[ProcessInfo] = []
    show_process_map: bool = False
    is_discovering: bool = False
    discovery_error: str = ""
    selected_process_id: str = ""

    @rx.var
    def show_map_or_discovering(self) -> bool:
        """Combined flag for CSS display (avoids | operator on Vars)."""
        return self.show_process_map or self.is_discovering

    @rx.event(background=True)
    async def run_discovery(self):
        """Run process discovery by building connector + schema directly from DBState."""
        async with self:
            self.is_discovering = True
            self.discovery_error = ""

        try:
            # Get connection info from DBState (serialized fields only, no _ vars)
            from biai.state.database import DBState

            async with self:
                db_state = await self.get_state(DBState)

            is_connected = False
            db_type_str = ""
            connector = None
            async with db_state:
                is_connected = db_state.is_connected
                db_type_str = db_state.db_type
                connector = await db_state.get_connector()

            if not is_connected or not connector:
                async with self:
                    self.discovery_error = "No active database connection. Connect first."
                    self.is_discovering = False
                return

            # Get model config
            from biai.state.model import ModelState

            async with self:
                model_state = await self.get_state(ModelState)

            ollama_host = ""
            ollama_model = ""
            async with model_state:
                ollama_host = model_state.ollama_host
                ollama_model = model_state.selected_model

            # Get selected schema from SchemaState
            from biai.state.schema import SchemaState

            async with self:
                schema_state = await self.get_state(SchemaState)
            selected_schema = ""
            async with schema_state:
                selected_schema = schema_state.selected_schema

            # Build schema snapshot
            from biai.db.schema_manager import SchemaManager

            schema_mgr = SchemaManager(connector)
            schema = await schema_mgr.get_snapshot(schema=selected_schema)

            # Run discovery
            from biai.ai.process_discovery import ProcessDiscoveryEngine

            engine = ProcessDiscoveryEngine(
                connector, schema,
                ollama_host=ollama_host,
                ollama_model=ollama_model,
                schema_name=schema.schema_name if schema.schema_name != "USER" else "",
            )
            discovered = await engine.discover()

            # Assign domain from graph communities
            communities: dict[str, int] = {}
            try:
                from biai.ai.metadata_graph import SchemaGraph
                graph = SchemaGraph(schema)
                communities = graph.find_table_communities()
            except Exception:
                pass

            async with self:
                if discovered:
                    proc_infos = []
                    for p in discovered:
                        # Determine domain from community of main table
                        domain = ""
                        if communities and p.tables:
                            main_table = p.tables[0].upper()
                            community_id = communities.get(main_table, -1)
                            if community_id >= 0:
                                domain = f"Domain {community_id}"
                        proc_infos.append(ProcessInfo(
                            id=p.id,
                            name=p.name,
                            description=getattr(p, "description", ""),
                            stages=[s.name if hasattr(s, "name") else str(s) for s in getattr(p, "stages", [])],
                            tables=getattr(p, "tables", []),
                            confidence=getattr(p, "confidence", 0.0),
                            evidence=[
                                EvidenceInfo(
                                    signal_type=e.signal_type,
                                    description=e.description,
                                    strength=e.strength,
                                )
                                for e in getattr(p, "evidence", [])
                            ],
                            domain=domain,
                        ))
                    self.discovered_processes = proc_infos
                    self.show_process_map = True
                    logger.info("process_map_discovery_done", count=len(discovered))
                else:
                    self.discovery_error = "No business processes found in this database."
                    self.show_process_map = False
                self.is_discovering = False

        except Exception as e:
            logger.error("process_map_discovery_error", error=str(e))
            async with self:
                self.discovery_error = f"Discovery failed: {e}"
                self.is_discovering = False

    def select_process(self, process_id: str):
        """Select a discovered process for drill-down."""
        self.selected_process_id = process_id

    def clear_selection(self):
        """Clear process selection."""
        self.selected_process_id = ""

    @rx.var
    def suggested_queries(self) -> list[str]:
        """Generate suggested SQL questions for the selected process."""
        if not self.selected_process_id:
            return []
        for p in self.discovered_processes:
            if p.id == self.selected_process_id:
                queries = []
                if p.tables:
                    main_table = p.tables[0]
                    queries.append(f"Show all records from {main_table}")
                if p.stages:
                    queries.append(f"How many records are in each {p.name} stage?")
                    queries.append(f"What is the average time between {p.name} stages?")
                if len(p.tables) > 1:
                    queries.append(f"Show {p.name} flow across {', '.join(p.tables[:3])}")
                return queries
        return []

    def hide_map(self):
        """Hide process map."""
        self.show_process_map = False

    @rx.var
    def has_processes(self) -> bool:
        return len(self.discovered_processes) > 0

    @rx.var
    def process_count(self) -> int:
        return len(self.discovered_processes)

    @rx.var
    def selected_process(self) -> dict:
        """Get the currently selected process data."""
        if not self.selected_process_id:
            return {}
        for p in self.discovered_processes:
            if p.id == self.selected_process_id:
                return {"id": p.id, "name": p.name, "description": p.description}
        return {}
