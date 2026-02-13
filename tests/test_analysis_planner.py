"""Tests for AnalysisPlanner and AnalysisExecutor — multi-step analysis."""

import json

import pandas as pd
import pytest

from biai.ai.analysis_planner import AnalysisPlanner
from biai.ai.analysis_executor import AnalysisExecutor, StepResult
from biai.models.analysis import AnalysisPlan, AnalysisStep, StepType, StepStatus


class TestMightBeComplex:
    """Test _might_be_complex() heuristic."""

    def test_simple_question(self):
        assert not AnalysisPlanner._might_be_complex("Show me all customers")

    def test_compare_keyword(self):
        assert AnalysisPlanner._might_be_complex("Compare sales Q1 vs Q2")

    def test_polish_compare(self):
        assert AnalysisPlanner._might_be_complex("Porównaj sprzedaż w Q1 i Q2")

    def test_vs_keyword(self):
        assert AnalysisPlanner._might_be_complex("Revenue 2024 vs 2023")

    def test_both_keyword(self):
        assert AnalysisPlanner._might_be_complex("Show both revenue and costs")

    def test_then_show(self):
        assert AnalysisPlanner._might_be_complex("Get customers then show their orders")

    def test_correlation_keyword(self):
        assert AnalysisPlanner._might_be_complex("Check correlation between price and sales")

    def test_and_also(self):
        assert AnalysisPlanner._might_be_complex("Show revenue and also count orders")

    def test_case_insensitive(self):
        assert AnalysisPlanner._might_be_complex("COMPARE sales by region")

    def test_polish_both(self):
        assert AnalysisPlanner._might_be_complex("Pokaż oba wyniki")


class TestParsePlan:
    """Test _parse_plan() JSON parsing."""

    def test_parse_valid_plan(self):
        raw = json.dumps({
            "is_complex": True,
            "steps": [
                {
                    "step": 1,
                    "type": "sql",
                    "description": "Get Q1 sales",
                    "depends_on": [],
                    "question_for_sql": "Show sales for Q1 2024",
                },
                {
                    "step": 2,
                    "type": "sql",
                    "description": "Get Q2 sales",
                    "depends_on": [],
                    "question_for_sql": "Show sales for Q2 2024",
                },
                {
                    "step": 3,
                    "type": "compare",
                    "description": "Compare Q1 vs Q2",
                    "depends_on": [1, 2],
                    "question_for_sql": "Show combined results",
                },
            ],
            "final_combination": "concat",
        })
        plan = AnalysisPlanner._parse_plan(raw)
        assert plan.is_complex is True
        assert len(plan.steps) == 3
        assert plan.steps[0].type == StepType.SQL
        assert plan.steps[2].type == StepType.COMPARE
        assert plan.steps[2].depends_on == [1, 2]

    def test_parse_json_in_markdown(self):
        raw = """Here is the plan:
```json
{
  "is_complex": false,
  "steps": [
    {"step": 1, "type": "sql", "description": "Direct query", "depends_on": [], "question_for_sql": "Show customers"}
  ]
}
```
"""
        plan = AnalysisPlanner._parse_plan(raw)
        assert len(plan.steps) == 1
        assert plan.steps[0].question_for_sql == "Show customers"

    def test_parse_invalid_json_raises(self):
        with pytest.raises(Exception):
            AnalysisPlanner._parse_plan("not json")

    def test_parse_empty_steps(self):
        raw = json.dumps({"is_complex": False, "steps": []})
        plan = AnalysisPlanner._parse_plan(raw)
        assert len(plan.steps) == 0
        assert plan.is_complex is False

    def test_parse_single_step_not_complex(self):
        raw = json.dumps({
            "is_complex": False,
            "steps": [
                {"step": 1, "type": "sql", "description": "Simple query",
                 "depends_on": [], "question_for_sql": "Show all orders"}
            ],
        })
        plan = AnalysisPlanner._parse_plan(raw)
        assert plan.is_complex is False


class TestDepContext:
    """Test AnalysisExecutor._build_dep_context()."""

    def test_build_with_results(self):
        step_outputs = {
            1: pd.DataFrame({"name": ["Alice", "Bob"], "score": [90, 85]}),
        }
        ctx = AnalysisExecutor._build_dep_context([1], step_outputs)
        assert "Results from step 1" in ctx
        assert "2 rows" in ctx
        assert "name, score" in ctx
        assert "Alice" in ctx

    def test_build_missing_dependency(self):
        step_outputs = {}
        ctx = AnalysisExecutor._build_dep_context([1], step_outputs)
        assert ctx == ""

    def test_build_empty_df_dependency(self):
        step_outputs = {1: pd.DataFrame()}
        ctx = AnalysisExecutor._build_dep_context([1], step_outputs)
        assert ctx == ""

    def test_build_multiple_dependencies(self):
        step_outputs = {
            1: pd.DataFrame({"a": [1, 2]}),
            2: pd.DataFrame({"b": [3, 4]}),
        }
        ctx = AnalysisExecutor._build_dep_context([1, 2], step_outputs)
        assert "step 1" in ctx
        assert "step 2" in ctx

    def test_build_limits_to_5_rows(self):
        step_outputs = {
            1: pd.DataFrame({"x": range(100)}),
        }
        ctx = AnalysisExecutor._build_dep_context([1], step_outputs)
        # head(5) limits preview
        lines = ctx.split("\n")
        # Should have header + context header + 5 data rows (not 100)
        assert len(lines) < 15


class TestContextQuestion:
    """Test _build_context_question() from pipeline."""

    def test_no_context_returns_original(self):
        from biai.ai.pipeline import AIPipeline
        result = AIPipeline._build_context_question("Show orders", [])
        assert result == "Show orders"

    def test_with_context_enriches(self):
        from biai.ai.pipeline import AIPipeline
        context = [
            {"question": "Show sales", "sql": "SELECT * FROM sales", "row_count": 10, "columns": ["id", "amount"]},
        ]
        result = AIPipeline._build_context_question("And for Q2?", context)
        assert "And for Q2?" in result
        assert "Show sales" in result
        assert "10 rows" in result

    def test_context_limits_to_3(self):
        from biai.ai.pipeline import AIPipeline
        context = [
            {"question": f"Q{i}", "sql": f"SELECT {i}", "row_count": i, "columns": []}
            for i in range(10)
        ]
        result = AIPipeline._build_context_question("Next?", context)
        # Should only include last 3 exchanges
        assert "Q7" in result or "Q8" in result or "Q9" in result
        assert "Q0" not in result
