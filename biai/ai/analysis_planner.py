"""Multi-step analysis planner — decomposes complex questions into steps."""

import json

import httpx

from biai.ai.prompt_templates import ANALYSIS_PLAN_PROMPT
from biai.models.analysis import AnalysisPlan, AnalysisStep, StepType
from biai.models.schema import SchemaSnapshot
from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, LLM_OPTIONS
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisPlanner:
    """Uses LLM to decompose complex questions into SQL steps."""

    def __init__(
        self,
        ollama_host: str = DEFAULT_OLLAMA_HOST,
        ollama_model: str = DEFAULT_MODEL,
    ):
        self._ollama_host = ollama_host
        self._ollama_model = ollama_model

    async def plan(
        self,
        question: str,
        schema: SchemaSnapshot | None = None,
        context: list[dict] | None = None,
    ) -> AnalysisPlan:
        """Analyze question and create execution plan."""
        # Quick heuristic: single-step questions
        if not self._might_be_complex(question):
            return AnalysisPlan(
                is_complex=False,
                steps=[AnalysisStep(
                    step=1, type=StepType.SQL,
                    description="Direct query",
                    question_for_sql=question,
                )],
            )

        schema_summary = ""
        if schema:
            parts = []
            for t in schema.tables[:20]:
                cols = ", ".join(c.name for c in t.columns[:10])
                parts.append(f"- {t.full_name}: {cols}")
            schema_summary = "\n".join(parts)

        ctx_text = ""
        if context:
            ctx_text = "\n".join(
                f"Previous: {c['question'][:80]} -> {c['row_count']} rows"
                for c in context[-3:]
            )

        prompt = ANALYSIS_PLAN_PROMPT.format(
            question=question,
            schema_summary=schema_summary or "(schema not available)",
            context=ctx_text or "(no previous context)",
        )

        try:
            raw = await self._call_llm(prompt)
            return self._parse_plan(raw)
        except Exception as e:
            logger.warning("analysis_plan_failed", error=str(e))
            return AnalysisPlan(
                is_complex=False,
                steps=[AnalysisStep(
                    step=1, type=StepType.SQL,
                    description="Direct query (planning failed)",
                    question_for_sql=question,
                )],
            )

    @staticmethod
    def _might_be_complex(question: str) -> bool:
        """Heuristic check if question might need multi-step analysis."""
        q = question.lower()
        complex_indicators = [
            "compare", "porównaj", "vs", "versus",
            "and also", "i również", "a także",
            "then show", "potem pokaż",
            "correlation", "korelacja",
            "trend and", "trend i",
            "both", "oba", "obie",
        ]
        return any(ind in q for ind in complex_indicators)

    async def _call_llm(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._ollama_host}/api/generate",
                json={
                    "model": self._ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": LLM_OPTIONS,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

    @staticmethod
    def _parse_plan(raw: str) -> AnalysisPlan:
        """Parse LLM response into AnalysisPlan."""
        json_str = raw
        if "```" in raw:
            for part in raw.split("```"):
                s = part.strip()
                if s.startswith("json"):
                    s = s[4:].strip()
                if s.startswith("{"):
                    json_str = s
                    break

        data = json.loads(json_str)
        steps = []
        for sd in data.get("steps", []):
            steps.append(AnalysisStep(
                step=sd.get("step", len(steps) + 1),
                type=StepType(sd.get("type", "sql")),
                description=sd.get("description", ""),
                depends_on=sd.get("depends_on", []),
                question_for_sql=sd.get("question_for_sql", ""),
            ))

        return AnalysisPlan(
            is_complex=data.get("is_complex", len(steps) > 1),
            steps=steps,
            final_combination=data.get("final_combination", ""),
        )
