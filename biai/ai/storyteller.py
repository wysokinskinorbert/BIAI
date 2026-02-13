"""Data Storyteller — generates narrative from analysis results."""

import json
import re

import httpx
import pandas as pd

from biai.ai.prompt_templates import STORYTELLING_PROMPT
from biai.models.insight import Insight
from biai.models.story import DataStory, StoryNarrativeType
from biai.utils.logger import get_logger

logger = get_logger(__name__)


class DataStoryteller:
    """Generates data narratives from query results and insights."""

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5-coder:7b-instruct-q4_K_M",
    ):
        self._host = ollama_host
        self._model = ollama_model

    async def generate_story(
        self,
        question: str,
        df: pd.DataFrame,
        insights: list[Insight] | None = None,
    ) -> DataStory:
        """Generate a data narrative from results."""
        findings = self._extract_findings(df, question)
        insight_text = ""
        if insights:
            insight_text = "\n".join(
                f"- [{i.type.value}] {i.title}: {i.description}" for i in insights
            )

        prompt = STORYTELLING_PROMPT.format(
            question=question,
            findings=findings,
            insights=insight_text or "No specific insights detected.",
        )

        try:
            raw = await self._call_llm(prompt)
            return self._parse_narrative(raw, question)
        except Exception as e:
            logger.warning("storyteller_failed", error=str(e))
            return self._fallback_story(question, df)

    def _extract_findings(self, df: pd.DataFrame, question: str) -> str:
        """Extract key findings from DataFrame for the prompt."""
        if df.empty:
            return "No data returned."

        parts = [f"Rows: {len(df)}, Columns: {', '.join(df.columns)}"]

        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        for col in num_cols[:4]:
            series = df[col].dropna()
            if series.empty:
                continue
            parts.append(
                f"{col}: min={series.min():.2f}, max={series.max():.2f}, "
                f"avg={series.mean():.2f}, sum={series.sum():.2f}"
            )

        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
        for col in cat_cols[:2]:
            top = df[col].value_counts().head(3)
            if not top.empty:
                top_str = ", ".join(f"{k}={v}" for k, v in top.items())
                parts.append(f"{col} top values: {top_str}")

        return "\n".join(parts)

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama for narrative generation."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._host}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 500},
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

    def _parse_narrative(self, raw: str, question: str) -> DataStory:
        """Parse LLM output into DataStory."""
        story = DataStory(raw_text=raw)

        # Detect narrative type from question
        q_lower = question.lower()
        if any(w in q_lower for w in ("trend", "over time", "monthly", "growth")):
            story.narrative_type = StoryNarrativeType.TREND
        elif any(w in q_lower for w in ("compare", "vs", "versus", "difference")):
            story.narrative_type = StoryNarrativeType.COMPARISON
        elif any(w in q_lower for w in ("anomaly", "outlier", "unusual", "spike")):
            story.narrative_type = StoryNarrativeType.ANOMALY
        elif any(w in q_lower for w in ("distribution", "breakdown", "share")):
            story.narrative_type = StoryNarrativeType.DISTRIBUTION

        # Parse sections from LLM output
        sections = {
            "context": "",
            "key_findings": [],
            "implications": "",
            "recommendations": [],
        }

        current_section = None
        for line in raw.split("\n"):
            line_stripped = line.strip()
            lower_line = line_stripped.lower()

            if "context" in lower_line and (lower_line.startswith("#") or lower_line.startswith("**")):
                current_section = "context"
                continue
            elif "finding" in lower_line and (lower_line.startswith("#") or lower_line.startswith("**")):
                current_section = "findings"
                continue
            elif "implication" in lower_line and (lower_line.startswith("#") or lower_line.startswith("**")):
                current_section = "implications"
                continue
            elif "recommendation" in lower_line and (lower_line.startswith("#") or lower_line.startswith("**")):
                current_section = "recommendations"
                continue

            if not line_stripped:
                continue

            # Remove markdown bullet markers
            content = re.sub(r"^[-*•]\s*", "", line_stripped)
            content = re.sub(r"^\d+\.\s*", "", content)
            content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)  # strip bold

            if current_section == "context":
                sections["context"] += " " + content if sections["context"] else content
            elif current_section == "findings":
                if content:
                    sections["key_findings"].append(content)
            elif current_section == "implications":
                sections["implications"] += " " + content if sections["implications"] else content
            elif current_section == "recommendations":
                if content:
                    sections["recommendations"].append(content)

        story.context = sections["context"].strip()
        story.key_findings = sections["key_findings"][:5]
        story.implications = sections["implications"].strip()
        story.recommendations = sections["recommendations"][:3]

        # Fallback: if parsing failed, use raw text as context
        if not story.context and not story.key_findings:
            story.context = raw.strip()[:500]

        return story

    def _fallback_story(self, question: str, df: pd.DataFrame) -> DataStory:
        """Generate minimal story without LLM."""
        findings = []
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if num_cols:
            col = num_cols[0]
            findings.append(
                f"Total {col}: {df[col].sum():,.2f} across {len(df)} records"
            )
            if len(df) > 1:
                findings.append(
                    f"Average {col}: {df[col].mean():,.2f} "
                    f"(range: {df[col].min():,.2f} — {df[col].max():,.2f})"
                )

        return DataStory(
            narrative_type=StoryNarrativeType.GENERAL,
            context=f"Analysis of: {question}",
            key_findings=findings or ["Query returned data for review."],
            implications="Further analysis may reveal additional patterns.",
            recommendations=["Review the data table for detailed records."],
            raw_text="\n".join(findings),
        )
