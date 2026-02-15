"""AI-powered Business Glossary Generator — LLM interprets table/column names."""

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from biai.ai.language import normalize_response_language, response_language_instruction
from biai.models.schema import SchemaSnapshot
from biai.models.glossary import BusinessGlossary, TableDescription, ColumnDescription
from biai.models.profile import TableProfile
from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, LLM_OPTIONS
from biai.utils.logger import get_logger

logger = get_logger(__name__)

_BIAI_DIR = Path.home() / ".biai"

GLOSSARY_PROMPT = """Analyze this database schema and generate business-friendly descriptions.

**Schema DDL:**
{schema_ddl}

{profiles_section}

Respond in this exact JSON format:
{{
  "tables": [
    {{
      "name": "table_name",
      "description": "2-3 sentence business description",
      "business_name": "Human-Friendly Table Name",
      "business_domain": "Sales|HR|Inventory|Finance|Operations|Customer|Product|Other",
      "columns": [
        {{
          "name": "column_name",
          "description": "What this column means in business context",
          "business_name": "Friendly Column Name",
          "examples": "Brief explanation of typical values"
        }}
      ]
    }}
  ]
}}

Guidelines:
- Describe what each table/column MEANS for a business user who doesn't know SQL
- business_name should be short (2-4 words), human-friendly
- business_domain categorizes the table's purpose
- For columns with abbreviations (e.g., ltv, qty, sku), spell out the full meaning
- For status/category columns, explain the possible values if visible in profiles
- Keep descriptions concise but informative
{language_instruction}
"""


class BusinessGlossaryGenerator:
    """Generates business glossary using LLM interpretation of schema + profiles."""

    def __init__(
        self,
        ollama_host: str = DEFAULT_OLLAMA_HOST,
        ollama_model: str = DEFAULT_MODEL,
        response_language: str = "pl",
    ):
        self._ollama_host = ollama_host
        self._ollama_model = ollama_model
        self._response_language = normalize_response_language(response_language)

    async def generate(
        self,
        schema: SchemaSnapshot,
        profiles: dict[str, TableProfile] | None = None,
    ) -> BusinessGlossary:
        """Generate business glossary from schema + optional profiles."""
        # Build DDL
        ddl_parts = []
        for table in schema.tables:
            ddl_parts.append(table.get_ddl())
        schema_ddl = "\n\n".join(ddl_parts)

        # Build profiles section
        profiles_section = ""
        if profiles:
            profile_lines = []
            for tname, tprof in profiles.items():
                for cp in tprof.column_profiles:
                    if cp.stats.top_values:
                        top_vals = ", ".join(
                            f"{v['value']} ({v['count']})" for v in cp.stats.top_values[:5]
                        )
                        profile_lines.append(f"- {tname}.{cp.column_name}: top values = {top_vals}")
                    if cp.semantic_type.value not in ("unknown", "text", "numeric"):
                        profile_lines.append(
                            f"- {tname}.{cp.column_name}: detected type = {cp.semantic_type.value}"
                        )
            if profile_lines:
                profiles_section = "**Column profiles (sample data insights):**\n" + "\n".join(profile_lines)

        prompt = GLOSSARY_PROMPT.format(
            schema_ddl=schema_ddl,
            profiles_section=profiles_section,
            language_instruction=response_language_instruction(self._response_language),
        )

        try:
            raw = await self._call_llm(prompt)
            glossary = self._parse_response(raw, schema)
        except Exception as e:
            logger.error("glossary_generation_failed", error=str(e))
            glossary = self._fallback_glossary(schema)

        glossary.db_name = schema.db_type or "unknown"
        glossary.generated_at = datetime.now(timezone.utc).isoformat()

        # Cache to disk
        self._save_cache(glossary)

        return glossary

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama to generate glossary."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._ollama_host}/api/generate",
                json={
                    "model": self._ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": LLM_OPTIONS,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

    def _parse_response(self, raw: str, schema: SchemaSnapshot) -> BusinessGlossary:
        """Parse LLM JSON response into BusinessGlossary."""
        # Extract JSON from response
        json_str = raw
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                stripped = part.strip()
                if stripped.startswith("json"):
                    stripped = stripped[4:].strip()
                if stripped.startswith("{"):
                    json_str = stripped
                    break

        data = json.loads(json_str)
        tables = []
        for td in data.get("tables", []):
            cols = [
                ColumnDescription(
                    name=cd.get("name", ""),
                    description=cd.get("description", ""),
                    business_name=cd.get("business_name", ""),
                    examples=cd.get("examples", ""),
                )
                for cd in td.get("columns", [])
            ]
            tables.append(TableDescription(
                name=td.get("name", ""),
                description=td.get("description", ""),
                business_name=td.get("business_name", ""),
                business_domain=td.get("business_domain", "Other"),
                columns=cols,
            ))

        return BusinessGlossary(tables=tables)

    @staticmethod
    def _fallback_glossary(schema: SchemaSnapshot) -> BusinessGlossary:
        """Generate minimal glossary without LLM (column names as-is)."""
        tables = []
        for t in schema.tables:
            cols = [
                ColumnDescription(
                    name=c.name,
                    description=c.comment or "",
                    business_name=c.name.replace("_", " ").title(),
                )
                for c in t.columns
            ]
            tables.append(TableDescription(
                name=t.name,
                description=t.comment or "",
                business_name=t.name.replace("_", " ").title(),
                columns=cols,
            ))
        return BusinessGlossary(tables=tables)

    @staticmethod
    def _save_cache(glossary: BusinessGlossary):
        """Save glossary to ~/.biai/glossary_{db_name}.json."""
        _BIAI_DIR.mkdir(parents=True, exist_ok=True)
        path = _BIAI_DIR / f"glossary_{glossary.db_name}.json"
        path.write_text(
            glossary.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("glossary_cached", path=str(path))

    @staticmethod
    def load_cache(db_name: str) -> BusinessGlossary | None:
        """Load cached glossary if available."""
        path = _BIAI_DIR / f"glossary_{db_name}.json"
        if not path.exists():
            return None
        try:
            return BusinessGlossary.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None
