"""Tests for ECharts option builder."""

import pandas as pd
import pytest

from biai.ai.echarts_builder import build_echarts_option, can_use_echarts
from biai.models.chart import ChartConfig, ChartType


class TestCanUseEcharts:
    def test_bar_supported(self):
        assert can_use_echarts(ChartType.BAR)

    def test_line_supported(self):
        assert can_use_echarts(ChartType.LINE)

    def test_pie_supported(self):
        assert can_use_echarts(ChartType.PIE)

    def test_heatmap_supported(self):
        assert can_use_echarts(ChartType.HEATMAP)

    def test_gauge_supported(self):
        assert can_use_echarts(ChartType.GAUGE)

    def test_funnel_supported(self):
        assert can_use_echarts(ChartType.FUNNEL)

    def test_waterfall_supported(self):
        assert can_use_echarts(ChartType.WATERFALL)

    def test_table_not_supported(self):
        assert not can_use_echarts(ChartType.TABLE)

    def test_sankey_supported(self):
        assert can_use_echarts(ChartType.SANKEY)


class TestBuildEchartsOption:
    def test_bar_chart(self):
        df = pd.DataFrame({"cat": ["A", "B", "C"], "val": [10, 20, 30]})
        config = ChartConfig(chart_type=ChartType.BAR, x_column="cat", y_columns=["val"])
        opt = build_echarts_option(config, df)
        assert opt
        assert opt["series"][0]["type"] == "bar"
        assert len(opt["series"][0]["data"]) == 3

    def test_horizontal_bar(self):
        df = pd.DataFrame({"cat": list("ABCDEF"), "val": range(6)})
        config = ChartConfig(chart_type=ChartType.BAR, x_column="cat", y_columns=["val"], horizontal=True)
        opt = build_echarts_option(config, df)
        assert opt
        assert opt["yAxis"]["type"] == "category"
        assert opt["xAxis"]["type"] == "value"

    def test_grouped_bar(self):
        df = pd.DataFrame({
            "cat": ["A", "A", "B", "B"],
            "grp": ["X", "Y", "X", "Y"],
            "val": [10, 20, 30, 40],
        })
        config = ChartConfig(chart_type=ChartType.BAR, x_column="cat", y_columns=["val"], group_column="grp")
        opt = build_echarts_option(config, df)
        assert opt
        assert len(opt["series"]) == 2  # X and Y groups
        assert opt["series"][0]["name"] == "X"

    def test_pie_chart(self):
        df = pd.DataFrame({"name": ["A", "B"], "val": [60, 40]})
        config = ChartConfig(chart_type=ChartType.PIE, x_column="name", y_columns=["val"])
        opt = build_echarts_option(config, df)
        assert opt
        assert opt["series"][0]["type"] == "pie"

    def test_line_chart(self):
        df = pd.DataFrame({"month": ["Jan", "Feb", "Mar"], "sales": [100, 200, 300]})
        config = ChartConfig(chart_type=ChartType.LINE, x_column="month", y_columns=["sales"])
        opt = build_echarts_option(config, df)
        assert opt
        assert opt["series"][0]["type"] == "line"

    def test_gauge_chart(self):
        df = pd.DataFrame({"rate": [75.5]})
        config = ChartConfig(chart_type=ChartType.GAUGE, title="Completion Rate")
        opt = build_echarts_option(config, df)
        assert opt
        assert opt["series"][0]["type"] == "gauge"
        assert opt["series"][0]["data"][0]["value"] == 75.5

    def test_funnel_chart(self):
        df = pd.DataFrame({"stage": ["A", "B", "C"], "count": [100, 60, 20]})
        config = ChartConfig(chart_type=ChartType.FUNNEL, x_column="stage", y_columns=["count"])
        opt = build_echarts_option(config, df)
        assert opt
        assert opt["series"][0]["type"] == "funnel"

    def test_waterfall_chart(self):
        df = pd.DataFrame({"item": ["Rev", "Cost", "Tax"], "amount": [1000, -400, -100]})
        config = ChartConfig(chart_type=ChartType.WATERFALL, x_column="item", y_columns=["amount"])
        opt = build_echarts_option(config, df)
        assert opt
        assert len(opt["series"]) == 2  # base (transparent) + values
        # Should have Total appended
        assert opt["xAxis"]["data"][-1] == "Total"

    def test_heatmap_chart(self):
        rows = []
        for x in ["A", "B", "C"]:
            for y in ["X", "Y"]:
                rows.append({"cat1": x, "cat2": y, "val": 5})
        df = pd.DataFrame(rows)
        config = ChartConfig(chart_type=ChartType.HEATMAP, x_column="cat1", y_columns=["val"])
        opt = build_echarts_option(config, df)
        assert opt
        assert opt["series"][0]["type"] == "heatmap"

    def test_table_returns_empty(self):
        df = pd.DataFrame({"a": [1]})
        config = ChartConfig(chart_type=ChartType.TABLE)
        opt = build_echarts_option(config, df)
        assert opt == {}

    def test_missing_columns_returns_empty(self):
        df = pd.DataFrame({"a": [1, 2]})
        config = ChartConfig(chart_type=ChartType.BAR, x_column="missing", y_columns=["a"])
        opt = build_echarts_option(config, df)
        assert opt == {}

    def test_toolbox_present(self):
        df = pd.DataFrame({"cat": ["A", "B"], "val": [10, 20]})
        config = ChartConfig(chart_type=ChartType.BAR, x_column="cat", y_columns=["val"])
        opt = build_echarts_option(config, df)
        assert "toolbox" in opt
        assert "saveAsImage" in opt["toolbox"]["feature"]
