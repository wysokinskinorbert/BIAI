"""Build ECharts option dict from ChartConfig and DataFrame."""

import pandas as pd

from biai.models.chart import ChartConfig, ChartType

# Chart types that ECharts handles well (simple, common charts)
ECHARTS_TYPES = {ChartType.BAR, ChartType.LINE, ChartType.PIE, ChartType.SCATTER, ChartType.AREA}

# Dark theme colors matching the Plotly dark theme
_COLORS = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", "#3ba272", "#fc8452", "#9a60b4"]


def can_use_echarts(chart_type: ChartType) -> bool:
    """Check if ECharts can render this chart type."""
    return chart_type in ECHARTS_TYPES


def build_echarts_option(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts option dict from ChartConfig + DataFrame.

    Returns empty dict if chart cannot be built.
    """
    if config.chart_type == ChartType.TABLE:
        return {}

    if config.chart_type == ChartType.PIE:
        return _build_pie(config, df)

    # All other types need x/y columns
    x_col = config.x_column
    y_cols = [c for c in config.y_columns if c != x_col]

    if not x_col or not y_cols or x_col not in df.columns:
        return {}

    x_data = df[x_col].astype(str).tolist()

    if config.chart_type == ChartType.BAR:
        return _build_bar(config, df, x_data, y_cols)
    elif config.chart_type == ChartType.LINE:
        return _build_line(config, df, x_data, y_cols)
    elif config.chart_type == ChartType.AREA:
        return _build_area(config, df, x_data, y_cols)
    elif config.chart_type == ChartType.SCATTER:
        return _build_scatter(config, df, x_data, y_cols)

    return {}


def _base_option(title: str) -> dict:
    """Base ECharts option with dark theme styling."""
    return {
        "backgroundColor": "transparent",
        "title": {
            "text": title,
            "textStyle": {"color": "#e0e0e0", "fontSize": 14},
            "left": "center",
        },
        "tooltip": {"trigger": "axis"},
        "color": _COLORS,
        "textStyle": {"color": "#b0b0b0"},
    }


def _build_bar(config: ChartConfig, df: pd.DataFrame, x_data: list, y_cols: list[str]) -> dict:
    option = _base_option(config.title)
    option["xAxis"] = {
        "type": "category",
        "data": x_data,
        "axisLabel": {"color": "#999", "rotate": 30 if len(x_data) > 8 else 0},
        "axisLine": {"lineStyle": {"color": "#555"}},
    }
    option["yAxis"] = {
        "type": "value",
        "axisLabel": {"color": "#999"},
        "splitLine": {"lineStyle": {"color": "#333"}},
    }
    option["grid"] = {"left": "10%", "right": "5%", "bottom": "15%", "top": "15%"}
    option["series"] = []
    for y_col in y_cols:
        if y_col in df.columns:
            option["series"].append({
                "name": y_col,
                "type": "bar",
                "data": df[y_col].tolist(),
                "emphasis": {"focus": "series"},
                "itemStyle": {"borderRadius": [4, 4, 0, 0]},
            })
    if len(option["series"]) > 1:
        option["legend"] = {"data": y_cols, "textStyle": {"color": "#ccc"}, "top": "bottom"}
        option["grid"]["bottom"] = "20%"
    option["tooltip"]["trigger"] = "axis"
    return option


def _build_line(config: ChartConfig, df: pd.DataFrame, x_data: list, y_cols: list[str]) -> dict:
    option = _base_option(config.title)
    option["xAxis"] = {
        "type": "category",
        "data": x_data,
        "axisLabel": {"color": "#999"},
        "axisLine": {"lineStyle": {"color": "#555"}},
    }
    option["yAxis"] = {
        "type": "value",
        "axisLabel": {"color": "#999"},
        "splitLine": {"lineStyle": {"color": "#333"}},
    }
    option["grid"] = {"left": "10%", "right": "5%", "bottom": "15%", "top": "15%"}
    option["series"] = []
    for y_col in y_cols:
        if y_col in df.columns:
            option["series"].append({
                "name": y_col,
                "type": "line",
                "data": df[y_col].tolist(),
                "smooth": True,
                "symbolSize": 6,
            })
    if len(option["series"]) > 1:
        option["legend"] = {"data": y_cols, "textStyle": {"color": "#ccc"}, "top": "bottom"}
        option["grid"]["bottom"] = "20%"
    return option


def _build_area(config: ChartConfig, df: pd.DataFrame, x_data: list, y_cols: list[str]) -> dict:
    option = _build_line(config, df, x_data, y_cols)
    for s in option.get("series", []):
        s["areaStyle"] = {"opacity": 0.3}
    return option


def _build_scatter(config: ChartConfig, df: pd.DataFrame, x_data: list, y_cols: list[str]) -> dict:
    option = _base_option(config.title)
    option["xAxis"] = {
        "type": "value",
        "axisLabel": {"color": "#999"},
        "splitLine": {"lineStyle": {"color": "#333"}},
    }
    option["yAxis"] = {
        "type": "value",
        "axisLabel": {"color": "#999"},
        "splitLine": {"lineStyle": {"color": "#333"}},
    }
    option["grid"] = {"left": "10%", "right": "5%", "bottom": "15%", "top": "15%"}
    option["tooltip"]["trigger"] = "item"
    option["series"] = []
    x_col = config.x_column
    for y_col in y_cols:
        if y_col in df.columns and x_col in df.columns:
            data_points = list(zip(df[x_col].tolist(), df[y_col].tolist()))
            option["series"].append({
                "name": y_col,
                "type": "scatter",
                "data": data_points,
                "symbolSize": 10,
            })
    return option


def _build_pie(config: ChartConfig, df: pd.DataFrame) -> dict:
    x_col = config.x_column
    y_cols = config.y_columns

    if not x_col or not y_cols or x_col not in df.columns:
        return {}
    if y_cols[0] not in df.columns:
        return {}

    labels = df[x_col].astype(str).tolist()
    values = df[y_cols[0]].tolist()

    pie_data = [{"name": name, "value": val} for name, val in zip(labels, values)]

    option = _base_option(config.title)
    option["tooltip"] = {"trigger": "item", "formatter": "{b}: {c} ({d}%)"}
    option["legend"] = {
        "orient": "vertical",
        "left": "left",
        "textStyle": {"color": "#ccc"},
    }
    option["series"] = [{
        "type": "pie",
        "radius": ["40%", "70%"],
        "avoidLabelOverlap": True,
        "itemStyle": {"borderRadius": 6, "borderColor": "#1a1a2e", "borderWidth": 2},
        "label": {"color": "#ccc"},
        "emphasis": {
            "label": {"show": True, "fontSize": 14, "fontWeight": "bold"},
        },
        "data": pie_data,
    }]
    return option
