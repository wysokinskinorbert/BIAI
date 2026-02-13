"""Process map state - shows discovered processes as interactive cards."""

import reflex as rx
from pydantic import BaseModel, Field

from biai.utils.logger import get_logger

logger = get_logger(__name__)


class ProcessInfo(BaseModel):
    """Serializable process info for rx.foreach rendering."""
    id: str = ""
    name: str = ""
    description: str = ""
    stages: list[str] = Field(default_factory=list)
    confidence: float = 0.0


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
                # _connector is transient, but accessible within same async with block
                connector = db_state._connector

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

            # Build schema snapshot
            from biai.db.schema_manager import SchemaManager

            schema_mgr = SchemaManager(connector)
            schema = await schema_mgr.get_snapshot()

            # Run discovery
            from biai.ai.process_discovery import ProcessDiscoveryEngine

            engine = ProcessDiscoveryEngine(
                connector, schema,
                ollama_host=ollama_host,
                ollama_model=ollama_model,
            )
            discovered = await engine.discover()

            async with self:
                if discovered:
                    self.discovered_processes = [
                        ProcessInfo(
                            id=str(i),
                            name=p.name,
                            description=getattr(p, "description", ""),
                            stages=[s.name if hasattr(s, "name") else str(s) for s in getattr(p, "stages", [])],
                            confidence=getattr(p, "confidence", 0.0),
                        )
                        for i, p in enumerate(discovered)
                    ]
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
