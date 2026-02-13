"""Build ECharts option dict from ChartConfig and DataFrame."""

import pandas as pd

from biai.models.chart import ChartConfig, ChartType

# Chart types that ECharts handles well
ECHARTS_TYPES = {
    ChartType.BAR, ChartType.LINE, ChartType.PIE, ChartType.SCATTER,
    ChartType.AREA, ChartType.HEATMAP, ChartType.GAUGE, ChartType.FUNNEL,
    ChartType.WATERFALL,
}

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

    if config.chart_type == ChartType.GAUGE:
        return _build_gauge(config, df)

    if config.chart_type == ChartType.FUNNEL:
        return _build_funnel(config, df)

    # All other types need x/y columns
    x_col = config.x_column
    y_cols = [c for c in config.y_columns if c != x_col]

    if not x_col or not y_cols or x_col not in df.columns:
        return {}

    x_data = df[x_col].astype(str).tolist()

    if config.chart_type == ChartType.BAR:
        # Grouped bars when group_column is set
        if config.group_column and config.group_column in df.columns:
            return _build_grouped_bar(config, df)
        return _build_bar(config, df, x_data, y_cols)
    elif config.chart_type == ChartType.LINE:
        return _build_line(config, df, x_data, y_cols)
    elif config.chart_type == ChartType.AREA:
        return _build_area(config, df, x_data, y_cols)
    elif config.chart_type == ChartType.SCATTER:
        return _build_scatter(config, df, x_data, y_cols)
    elif config.chart_type == ChartType.HEATMAP:
        return _build_heatmap(config, df)
    elif config.chart_type == ChartType.WATERFALL:
        return _build_waterfall(config, df, x_data, y_cols)

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
        "toolbox": {
            "show": True,
            "right": "5%",
            "top": "0%",
            "feature": {
                "saveAsImage": {
                    "title": "Save as PNG",
                    "pixelRatio": 2,
                    "backgroundColor": "#1a1a2e",
                },
            },
            "iconStyle": {"borderColor": "#666"},
        },
        "color": _COLORS,
        "textStyle": {"color": "#b0b0b0"},
    }


def _build_bar(config: ChartConfig, df: pd.DataFrame, x_data: list, y_cols: list[str]) -> dict:
    option = _base_option(config.title)
    horizontal = getattr(config, "horizontal", False)

    if horizontal:
        # Horizontal bars: swap axes, labels on left
        option["yAxis"] = {
            "type": "category",
            "data": x_data,
            "axisLabel": {"color": "#999", "width": 120, "overflow": "truncate"},
            "axisLine": {"lineStyle": {"color": "#555"}},
        }
        option["xAxis"] = {
            "type": "value",
            "axisLabel": {"color": "#999"},
            "splitLine": {"lineStyle": {"color": "#333"}},
        }
        option["grid"] = {"left": "25%", "right": "8%", "bottom": "10%", "top": "15%"}
        border_radius = [0, 4, 4, 0]
        label_pos = "right"
    else:
        option["xAxis"] = {
            "type": "category",
            "data": x_data,
            "axisLabel": {
                "color": "#999",
                "rotate": 45 if len(x_data) > 8 else 0,
                "interval": 0 if len(x_data) <= 20 else "auto",
            },
            "axisLine": {"lineStyle": {"color": "#555"}},
        }
        option["yAxis"] = {
            "type": "value",
            "axisLabel": {"color": "#999"},
            "splitLine": {"lineStyle": {"color": "#333"}},
        }
        option["grid"] = {
            "left": "10%", "right": "5%",
            "bottom": "20%" if len(x_data) > 8 else "15%",
            "top": "15%",
        }
        border_radius = [4, 4, 0, 0]
        label_pos = "top"

    option["series"] = []
    show_labels = len(x_data) <= 15
    for y_col in y_cols:
        if y_col in df.columns:
            series_item = {
                "name": y_col,
                "type": "bar",
                "data": df[y_col].tolist(),
                "emphasis": {"focus": "series"},
                "itemStyle": {"borderRadius": border_radius},
            }
            if show_labels:
                series_item["label"] = {
                    "show": True,
                    "position": label_pos,
                    "color": "#ccc",
                    "fontSize": 10,
                }
            option["series"].append(series_item)

    if len(option["series"]) > 1:
        option["legend"] = {"data": y_cols, "textStyle": {"color": "#ccc"}, "top": "bottom"}
        option["grid"]["bottom"] = "20%"
    option["tooltip"]["trigger"] = "axis"
    return option


def _build_grouped_bar(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build grouped bar chart from x_column + group_column + y_columns[0]."""
    x_col = config.x_column
    group_col = config.group_column
    val_col = config.y_columns[0] if config.y_columns else None

    if not x_col or not group_col or not val_col:
        return {}
    if any(c not in df.columns for c in (x_col, group_col, val_col)):
        return {}

    x_labels = df[x_col].unique().astype(str).tolist()
    groups = df[group_col].unique().astype(str).tolist()

    option = _base_option(config.title)
    option["xAxis"] = {
        "type": "category",
        "data": x_labels,
        "axisLabel": {
            "color": "#999",
            "rotate": 45 if len(x_labels) > 8 else 0,
            "interval": 0 if len(x_labels) <= 20 else "auto",
        },
        "axisLine": {"lineStyle": {"color": "#555"}},
    }
    option["yAxis"] = {
        "type": "value",
        "axisLabel": {"color": "#999"},
        "splitLine": {"lineStyle": {"color": "#333"}},
    }
    option["grid"] = {
        "left": "10%", "right": "5%",
        "bottom": "20%" if len(x_labels) > 8 else "15%",
        "top": "15%",
    }
    option["legend"] = {"data": groups, "textStyle": {"color": "#ccc"}, "top": "bottom"}
    option["grid"]["bottom"] = "20%"

    option["series"] = []
    for group in groups:
        group_df = df[df[group_col].astype(str) == group]
        # Build value list aligned with x_labels
        val_map = dict(zip(group_df[x_col].astype(str), group_df[val_col]))
        values = [val_map.get(x, 0) for x in x_labels]
        option["series"].append({
            "name": group,
            "type": "bar",
            "data": values,
            "emphasis": {"focus": "series"},
            "itemStyle": {"borderRadius": [4, 4, 0, 0]},
        })

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


def _build_gauge(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts gauge for single-value percentage/rate data."""
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not num_cols or df.empty:
        return {}
    value = float(df[num_cols[0]].iloc[0])
    max_val = 100 if value <= 100 else float(df[num_cols[0]].max()) * 1.2

    option = _base_option(config.title)
    option["series"] = [{
        "type": "gauge",
        "detail": {"valueAnimation": True, "formatter": "{value}", "fontSize": 20, "color": "#ccc"},
        "data": [{"value": round(value, 1), "name": num_cols[0]}],
        "max": max_val,
        "axisLine": {"lineStyle": {"width": 15, "color": [
            [0.3, "#ee6666"], [0.7, "#fac858"], [1, "#91cc75"],
        ]}},
        "axisTick": {"show": False},
        "splitLine": {"show": False},
        "axisLabel": {"color": "#999"},
        "pointer": {"itemStyle": {"color": "#5470c6"}},
        "title": {"color": "#ccc"},
    }]
    return option


def _build_funnel(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts funnel from category + value data."""
    x_col = config.x_column
    y_cols = config.y_columns

    if not x_col or not y_cols or x_col not in df.columns:
        return {}
    val_col = y_cols[0]
    if val_col not in df.columns:
        return {}

    labels = df[x_col].astype(str).tolist()
    values = df[val_col].tolist()
    funnel_data = [{"name": n, "value": v} for n, v in zip(labels, values)]
    # Sort descending for proper funnel shape
    funnel_data.sort(key=lambda d: d["value"], reverse=True)

    option = _base_option(config.title)
    option["tooltip"] = {"trigger": "item", "formatter": "{b}: {c}"}
    option["legend"] = {
        "data": labels,
        "textStyle": {"color": "#ccc"},
        "orient": "vertical",
        "left": "left",
    }
    option["series"] = [{
        "type": "funnel",
        "left": "20%",
        "width": "60%",
        "label": {"show": True, "position": "inside", "color": "#fff"},
        "emphasis": {"label": {"fontSize": 14}},
        "data": funnel_data,
    }]
    return option


def _build_heatmap(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts heatmap from 2-categorical + 1-numeric DataFrame."""
    if len(df.columns) < 3:
        return {}
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(cat_cols) < 2 or not num_cols:
        return {}

    x_col, y_col = cat_cols[0], cat_cols[1]
    val_col = num_cols[0]

    x_labels = sorted(df[x_col].unique().astype(str).tolist())
    y_labels = sorted(df[y_col].unique().astype(str).tolist())

    data_points = []
    for _, row in df.iterrows():
        xi = x_labels.index(str(row[x_col])) if str(row[x_col]) in x_labels else 0
        yi = y_labels.index(str(row[y_col])) if str(row[y_col]) in y_labels else 0
        data_points.append([xi, yi, float(row[val_col]) if pd.notna(row[val_col]) else 0])

    vals = [p[2] for p in data_points]
    min_val = min(vals) if vals else 0
    max_val = max(vals) if vals else 1

    option = _base_option(config.title)
    option["tooltip"] = {"position": "top"}
    option["grid"] = {"left": "15%", "right": "10%", "bottom": "20%", "top": "15%"}
    option["xAxis"] = {
        "type": "category",
        "data": x_labels,
        "axisLabel": {"color": "#999", "rotate": 30 if len(x_labels) > 6 else 0},
        "splitArea": {"show": True},
    }
    option["yAxis"] = {
        "type": "category",
        "data": y_labels,
        "axisLabel": {"color": "#999"},
        "splitArea": {"show": True},
    }
    option["visualMap"] = {
        "min": min_val,
        "max": max_val,
        "calculable": True,
        "orient": "horizontal",
        "left": "center",
        "bottom": "0%",
        "inRange": {"color": ["#313695", "#4575b4", "#74add1", "#abd9e9", "#fee090", "#fdae61", "#f46d43", "#d73027"]},
        "textStyle": {"color": "#ccc"},
    }
    option["series"] = [{
        "type": "heatmap",
        "data": data_points,
        "label": {"show": len(data_points) <= 50, "color": "#fff", "fontSize": 10},
        "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0, 0, 0, 0.5)"}},
    }]
    return option


def _build_waterfall(config: ChartConfig, df: pd.DataFrame, x_data: list, y_cols: list[str]) -> dict:
    """Build waterfall chart using stacked bars with transparent base."""
    if not y_cols or y_cols[0] not in df.columns:
        return {}

    values = df[y_cols[0]].tolist()
    # Compute cumulative base for each bar
    base = []
    running = 0
    for v in values:
        val = float(v) if v is not None else 0
        if val >= 0:
            base.append(running)
            running += val
        else:
            running += val
            base.append(running)

    # Add total bar
    x_data_ext = x_data + ["Total"]
    base_ext = base + [0]
    values_ext = [float(v) if v is not None else 0 for v in values] + [running]

    option = _base_option(config.title)
    option["xAxis"] = {
        "type": "category",
        "data": x_data_ext,
        "axisLabel": {"color": "#999", "rotate": 30 if len(x_data_ext) > 8 else 0},
        "axisLine": {"lineStyle": {"color": "#555"}},
    }
    option["yAxis"] = {
        "type": "value",
        "axisLabel": {"color": "#999"},
        "splitLine": {"lineStyle": {"color": "#333"}},
    }
    option["grid"] = {"left": "10%", "right": "5%", "bottom": "15%", "top": "15%"}
    option["tooltip"]["trigger"] = "axis"

    # Transparent base series (invisible)
    option["series"] = [
        {
            "name": "base",
            "type": "bar",
            "stack": "waterfall",
            "data": base_ext,
            "itemStyle": {"borderColor": "transparent", "color": "transparent"},
            "emphasis": {"itemStyle": {"borderColor": "transparent", "color": "transparent"}},
        },
        {
            "name": y_cols[0],
            "type": "bar",
            "stack": "waterfall",
            "data": [
                {
                    "value": abs(v),
                    "itemStyle": {
                        "color": "#91cc75" if v >= 0 else "#ee6666",
                        "borderRadius": [4, 4, 0, 0] if v >= 0 else [0, 0, 4, 4],
                    },
                }
                for v in values_ext
            ],
            "label": {
                "show": len(values_ext) <= 15,
                "position": "top",
                "color": "#ccc",
                "fontSize": 10,
                "formatter": "{c}",
            },
        },
    ]
    # Override total bar color
    total_item = option["series"][1]["data"][-1]
    total_item["itemStyle"]["color"] = "#5470c6"
    total_item["itemStyle"]["borderRadius"] = [4, 4, 0, 0]

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
