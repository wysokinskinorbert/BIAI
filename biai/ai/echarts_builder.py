"""Build ECharts option dict from ChartConfig and DataFrame."""

import pandas as pd

from biai.models.chart import ChartConfig, ChartType

# Chart types that ECharts handles well
ECHARTS_TYPES = {
    ChartType.BAR, ChartType.LINE, ChartType.PIE, ChartType.SCATTER,
    ChartType.AREA, ChartType.HEATMAP, ChartType.GAUGE, ChartType.FUNNEL,
    ChartType.WATERFALL, ChartType.TREEMAP, ChartType.SUNBURST,
    ChartType.RADAR, ChartType.PARALLEL, ChartType.SANKEY,
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

    if config.chart_type == ChartType.SANKEY:
        return _build_sankey(config, df)

    if config.chart_type == ChartType.PIE:
        return _build_pie(config, df)

    if config.chart_type == ChartType.GAUGE:
        return _build_gauge(config, df)

    if config.chart_type == ChartType.FUNNEL:
        return _build_funnel(config, df)

    if config.chart_type == ChartType.TREEMAP:
        return _build_treemap(config, df)

    if config.chart_type == ChartType.SUNBURST:
        return _build_sunburst(config, df)

    if config.chart_type == ChartType.RADAR:
        return _build_radar(config, df)

    if config.chart_type == ChartType.PARALLEL:
        return _build_parallel(config, df)

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


def _build_treemap(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts treemap for hierarchical data.

    Expects: 1+ categorical columns (hierarchy levels) + 1 numeric column (value).
    If 2 cat cols: parent-child grouping. If 1 cat col: flat treemap.
    """
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not cat_cols or not num_cols:
        return {}

    val_col = num_cols[0]

    option = _base_option(config.title)
    option["tooltip"] = {"formatter": "{b}: {c}"}

    if len(cat_cols) >= 2:
        # Hierarchical: first cat = parent, second = child
        parent_col, child_col = cat_cols[0], cat_cols[1]
        tree_data = []
        for parent, group in df.groupby(parent_col):
            children = []
            for _, row in group.iterrows():
                val = float(row[val_col]) if pd.notna(row[val_col]) else 0
                children.append({"name": str(row[child_col]), "value": abs(val)})
            tree_data.append({
                "name": str(parent),
                "children": children,
            })
    else:
        # Flat treemap
        tree_data = []
        for _, row in df.iterrows():
            val = float(row[val_col]) if pd.notna(row[val_col]) else 0
            tree_data.append({"name": str(row[cat_cols[0]]), "value": abs(val)})

    option["series"] = [{
        "type": "treemap",
        "data": tree_data,
        "roam": False,
        "breadcrumb": {"show": True, "itemStyle": {"color": "#333", "textStyle": {"color": "#ccc"}}},
        "label": {"show": True, "color": "#fff", "fontSize": 12},
        "itemStyle": {"borderColor": "#1a1a2e", "borderWidth": 2, "gapWidth": 2},
        "levels": [
            {"itemStyle": {"borderColor": "#555", "borderWidth": 3, "gapWidth": 3}},
            {"colorSaturation": [0.35, 0.6], "itemStyle": {"borderColorSaturation": 0.7, "gapWidth": 2}},
        ],
    }]
    return option


def _build_sunburst(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts sunburst for nested categorical data.

    Expects: 2+ categorical columns (hierarchy levels) + 1 numeric column.
    """
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if len(cat_cols) < 2 or not num_cols:
        # Fallback to flat sunburst if only 1 cat col
        if cat_cols and num_cols:
            return _build_flat_sunburst(config, df, cat_cols[0], num_cols[0])
        return {}

    val_col = num_cols[0]
    level1_col, level2_col = cat_cols[0], cat_cols[1]

    # Build hierarchy: level1 > level2
    data = []
    for parent, group in df.groupby(level1_col):
        children = []
        for _, row in group.iterrows():
            val = float(row[val_col]) if pd.notna(row[val_col]) else 0
            children.append({"name": str(row[level2_col]), "value": abs(val)})
        data.append({"name": str(parent), "children": children})

    option = _base_option(config.title)
    option["tooltip"] = {"trigger": "item", "formatter": "{b}: {c}"}
    option["series"] = [{
        "type": "sunburst",
        "data": data,
        "radius": ["15%", "80%"],
        "label": {"color": "#ccc", "fontSize": 11, "rotate": "radial"},
        "itemStyle": {"borderColor": "#1a1a2e", "borderWidth": 2},
        "emphasis": {"focus": "ancestor"},
        "levels": [
            {},
            {"r0": "15%", "r": "45%", "label": {"fontSize": 12}},
            {"r0": "45%", "r": "80%", "label": {"fontSize": 10}},
        ],
    }]
    return option


def _build_flat_sunburst(config: ChartConfig, df: pd.DataFrame, cat_col: str, val_col: str) -> dict:
    """Flat sunburst for single categorical column."""
    data = []
    for _, row in df.iterrows():
        val = float(row[val_col]) if pd.notna(row[val_col]) else 0
        data.append({"name": str(row[cat_col]), "value": abs(val)})

    option = _base_option(config.title)
    option["tooltip"] = {"trigger": "item"}
    option["series"] = [{
        "type": "sunburst",
        "data": data,
        "radius": ["20%", "75%"],
        "label": {"color": "#ccc"},
        "itemStyle": {"borderColor": "#1a1a2e", "borderWidth": 2},
    }]
    return option


def _build_radar(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts radar for multi-dimensional comparison.

    Expects: 1 categorical column (row labels) + 3+ numeric columns (dimensions).
    Best with < 10 rows.
    """
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if len(num_cols) < 3:
        return {}

    # Use up to 8 dimensions and 6 rows
    dimensions = num_cols[:8]
    plot_df = df.head(6)

    # Build indicator (axes) with max values
    indicators = []
    for col in dimensions:
        col_max = float(df[col].max()) if not df[col].dropna().empty else 100
        indicators.append({"name": col, "max": col_max * 1.2 if col_max > 0 else 100})

    # Build series data
    series_data = []
    for idx, row in plot_df.iterrows():
        label = str(row[cat_cols[0]]) if cat_cols else f"Row {idx}"
        values = [float(row[c]) if pd.notna(row[c]) else 0 for c in dimensions]
        series_data.append({"name": label, "value": values})

    option = _base_option(config.title)
    option["tooltip"] = {"trigger": "item"}
    option["legend"] = {
        "data": [d["name"] for d in series_data],
        "textStyle": {"color": "#ccc"},
        "bottom": 0,
    }
    option["radar"] = {
        "indicator": indicators,
        "shape": "polygon",
        "splitNumber": 4,
        "axisName": {"color": "#999", "fontSize": 11},
        "splitLine": {"lineStyle": {"color": "#444"}},
        "splitArea": {"show": True, "areaStyle": {"color": ["rgba(50,50,80,0.3)", "rgba(50,50,80,0.1)"]}},
        "axisLine": {"lineStyle": {"color": "#555"}},
    }
    option["series"] = [{
        "type": "radar",
        "data": series_data,
        "emphasis": {"lineStyle": {"width": 3}},
        "areaStyle": {"opacity": 0.15},
    }]
    return option


def _build_parallel(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts parallel coordinates for multi-dimensional analysis.

    Expects: 4+ numeric columns. Optional 1 categorical for color grouping.
    """
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    if len(num_cols) < 4:
        return {}

    dimensions = num_cols[:8]
    plot_df = df.head(200)  # limit rows for performance

    # Build parallel axes
    parallel_axis = []
    for i, col in enumerate(dimensions):
        parallel_axis.append({
            "dim": i,
            "name": col,
            "nameTextStyle": {"color": "#999", "fontSize": 11},
            "axisLabel": {"color": "#999"},
            "axisLine": {"lineStyle": {"color": "#555"}},
        })

    # Build data rows
    data = []
    for _, row in plot_df.iterrows():
        values = [float(row[c]) if pd.notna(row[c]) else 0 for c in dimensions]
        data.append(values)

    option = _base_option(config.title)
    option["parallelAxis"] = parallel_axis
    option["parallel"] = {
        "left": "5%",
        "right": "13%",
        "bottom": "10%",
        "top": "15%",
        "parallelAxisDefault": {
            "type": "value",
            "nameLocation": "end",
            "nameGap": 20,
            "axisLine": {"lineStyle": {"color": "#555"}},
            "axisTick": {"lineStyle": {"color": "#555"}},
            "splitLine": {"show": False},
            "axisLabel": {"color": "#999"},
        },
    }

    # If we have a categorical column, color-code by group
    if cat_cols:
        group_col = cat_cols[0]
        groups = plot_df[group_col].unique().tolist()[:6]
        option["legend"] = {
            "data": [str(g) for g in groups],
            "textStyle": {"color": "#ccc"},
            "bottom": 0,
        }
        option["series"] = []
        for gi, group in enumerate(groups):
            mask = plot_df[group_col] == group
            group_data = []
            for _, row in plot_df[mask].iterrows():
                group_data.append([float(row[c]) if pd.notna(row[c]) else 0 for c in dimensions])
            option["series"].append({
                "name": str(group),
                "type": "parallel",
                "data": group_data,
                "lineStyle": {"width": 1.5, "opacity": 0.5, "color": _COLORS[gi % len(_COLORS)]},
                "emphasis": {"lineStyle": {"width": 3, "opacity": 1}},
            })
    else:
        option["series"] = [{
            "type": "parallel",
            "data": data,
            "lineStyle": {"width": 1, "opacity": 0.4},
            "emphasis": {"lineStyle": {"width": 3, "opacity": 1}},
        }]

    option["tooltip"] = {"show": False}
    return option


def add_chart_annotations(option: dict, df: pd.DataFrame, insights: list[dict] | None = None) -> dict:
    """Add markPoint/markLine/markArea annotations to an existing ECharts option.

    Enhances charts with:
    - markPoint for min/max values
    - markLine for average + trend line (linear regression for line/area)
    - markArea for anomaly regions (if insights provided)
    - Percentage change label between first and last values (for line/area)
    """
    if not option or "series" not in option:
        return option

    # Ensure enough grid space for markLine/markPoint labels
    grid = option.setdefault("grid", {})
    if grid.get("right") in (None, "10%"):
        grid["right"] = "15%"

    is_first_series = True
    for series in option.get("series", []):
        stype = series.get("type", "")
        if stype not in ("bar", "line", "area"):
            continue

        # Add min/max points (offset above bars to avoid overlapping data labels)
        series.setdefault("markPoint", {})
        series["markPoint"]["data"] = [
            {"type": "max", "name": "Max", "itemStyle": {"color": "#91cc75"}},
            {"type": "min", "name": "Min", "itemStyle": {"color": "#ee6666"}},
        ]
        series["markPoint"]["symbolSize"] = 35
        series["markPoint"]["label"] = {"color": "#fff", "fontSize": 9}
        series["markPoint"]["symbolOffset"] = [0, -10]

        # Build markLine data — always include average
        mark_line_data: list = [
            {"type": "average", "name": "Avg", "lineStyle": {"color": "#fac858", "type": "dashed"}},
        ]

        # Add trend line for line/area charts with enough data points
        if stype in ("line", "area") and is_first_series:
            trend = _compute_trend_line(series, df)
            if trend:
                mark_line_data.append(trend)

        series.setdefault("markLine", {})
        series["markLine"]["data"] = mark_line_data
        series["markLine"]["label"] = {
            "color": "#fac858",
            "fontSize": 10,
            "position": "insideEndTop",
        }
        series["markLine"]["silent"] = True

        # Add percentage change label for first line/area series
        if stype in ("line", "area") and is_first_series:
            pct = _compute_percentage_change(series)
            if pct is not None:
                existing = series["markPoint"]["data"]
                color = "#91cc75" if pct >= 0 else "#ee6666"
                sign = "+" if pct >= 0 else ""
                existing.append({
                    "coord": _last_data_coord(series),
                    "value": f"{sign}{pct:.1f}%",
                    "symbol": "pin",
                    "symbolSize": 36,
                    "itemStyle": {"color": color},
                    "label": {"color": "#fff", "fontSize": 9},
                })

        is_first_series = False

    # Add anomaly markArea from insights if available
    if insights and option.get("series"):
        x_axis_data = _get_x_axis_labels(option)
        for insight in insights:
            if insight.get("type") != "anomaly":
                continue
            first_series = option["series"][0]
            if first_series.get("type") not in ("bar", "line", "area"):
                continue
            first_series.setdefault("markArea", {})
            first_series["markArea"].setdefault("data", [])
            first_series["markArea"]["silent"] = True
            first_series["markArea"]["itemStyle"] = {
                "color": "rgba(238, 102, 102, 0.10)",
            }
            # Place markArea at anomaly position if metadata has index
            meta = insight.get("metadata", {})
            idx = meta.get("index") or meta.get("position")
            if idx is not None and x_axis_data:
                try:
                    pos = int(idx)
                    if 0 <= pos < len(x_axis_data):
                        label = x_axis_data[pos]
                        first_series["markArea"]["data"].append([
                            {"xAxis": label, "itemStyle": {"color": "rgba(238, 102, 102, 0.15)"}},
                            {"xAxis": label},
                        ])
                except (ValueError, TypeError):
                    pass

    return option


def _compute_trend_line(series: dict, df: pd.DataFrame) -> dict | None:
    """Compute linear regression trend line as markLine start/end coords."""
    data = series.get("data", [])
    if not data or len(data) < 3:
        return None
    try:
        import numpy as np
        # Extract y-values (handle both plain values and [x,y] pairs)
        y_vals = []
        for d in data:
            if isinstance(d, (int, float)):
                y_vals.append(float(d))
            elif isinstance(d, (list, tuple)) and len(d) >= 2:
                y_vals.append(float(d[1]))
            else:
                return None
        if len(y_vals) < 3:
            return None
        x = np.arange(len(y_vals), dtype=float)
        y = np.array(y_vals, dtype=float)
        # Simple linear regression
        slope, intercept = np.polyfit(x, y, 1)
        return [
            {"coord": [0, round(float(intercept), 2)], "symbol": "none"},
            {
                "coord": [len(y_vals) - 1, round(float(slope * (len(y_vals) - 1) + intercept), 2)],
                "symbol": "none",
                "lineStyle": {"color": "#73c0de", "type": "dotted", "width": 2},
                "label": {"formatter": "Trend", "color": "#73c0de"},
            },
        ]
    except Exception:
        return None


def _compute_percentage_change(series: dict) -> float | None:
    """Compute percentage change between first and last data values."""
    data = series.get("data", [])
    if not data or len(data) < 2:
        return None
    try:
        def _val(d):
            if isinstance(d, (int, float)):
                return float(d)
            if isinstance(d, (list, tuple)) and len(d) >= 2:
                return float(d[1])
            return None

        first = _val(data[0])
        last = _val(data[-1])
        if first is None or last is None or first == 0:
            return None
        return ((last - first) / abs(first)) * 100
    except Exception:
        return None


def _last_data_coord(series: dict) -> list:
    """Get coordinate of the last data point for markPoint placement."""
    data = series.get("data", [])
    if not data:
        return [0, 0]
    idx = len(data) - 1
    d = data[-1]
    if isinstance(d, (int, float)):
        return [idx, float(d)]
    if isinstance(d, (list, tuple)) and len(d) >= 2:
        return [d[0], float(d[1])]
    return [idx, 0]


def _get_x_axis_labels(option: dict) -> list[str]:
    """Extract x-axis category labels from ECharts option."""
    x_axis = option.get("xAxis")
    if isinstance(x_axis, dict):
        return x_axis.get("data", [])
    if isinstance(x_axis, list) and x_axis:
        return x_axis[0].get("data", [])
    return []


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


def _build_sankey(config: ChartConfig, df: pd.DataFrame) -> dict:
    """Build ECharts Sankey from DataFrame with source/target/value columns."""
    cols = [c.lower() for c in df.columns]

    src_col = next(
        (c for c in df.columns if any(p in c.lower() for p in ["source", "from"])),
        None,
    )
    tgt_col = next(
        (c for c in df.columns if any(p in c.lower() for p in ["target", "to"])),
        None,
    )
    val_col = next(
        (c for c in df.columns if any(p in c.lower() for p in ["value", "count", "weight"])),
        None,
    )

    if not src_col or not tgt_col:
        return {}

    nodes_set: set[str] = set()
    links = []
    for _, row in df.iterrows():
        s = str(row[src_col])
        t = str(row[tgt_col])
        v = float(row[val_col]) if val_col and val_col in df.columns and pd.notna(row[val_col]) else 1
        nodes_set.add(s)
        nodes_set.add(t)
        links.append({"source": s, "target": t, "value": v})

    nodes = [{"name": n} for n in sorted(nodes_set)]
    return _build_sankey_option(config.title, nodes, links)


def build_sankey_from_event_log(event_log, title: str = "") -> dict:
    """Build ECharts Sankey option directly from an EventLog instance.

    Uses get_transition_matrix() for links and get_activities() for node ordering.
    """
    from biai.models.event_log import EventLog

    if not isinstance(event_log, EventLog) or not event_log.events:
        return {}

    transition_matrix = event_log.get_transition_matrix()
    if not transition_matrix:
        return {}

    activities = event_log.get_activities()
    nodes = [{"name": a} for a in activities]

    links = []
    for (fr, to), count in transition_matrix.items():
        links.append({"source": fr, "target": to, "value": count})

    return _build_sankey_option(
        title or f"Process Flow: {event_log.process_id}",
        nodes,
        links,
    )


def build_sankey_from_process_config(process_config) -> dict:
    """Build ECharts Sankey from ProcessFlowConfig edges.

    Uses process_config.edges (which have source, target, count) to build
    a Sankey transition flow. This works regardless of whether a DiscoveredProcess
    was matched — it uses the already-computed process graph data.

    ECharts Sankey requires a DAG (no cycles). Process flows often have cycles
    (e.g. resolved→reopened→investigating). Back-edges are handled by suffixing
    the target with " (return)" to create a separate node that breaks the cycle.
    """
    if not process_config or not process_config.edges:
        return {}

    # Map node IDs to labels
    id_to_label = {}
    for node in process_config.nodes:
        id_to_label[node.id] = node.label

    # Collect raw edges
    raw_edges: list[tuple[str, str, int]] = []
    for edge in process_config.edges:
        src = id_to_label.get(edge.source, edge.source)
        tgt = id_to_label.get(edge.target, edge.target)
        value = edge.count if edge.count and edge.count > 0 else 1
        raw_edges.append((src, tgt, value))

    # Break cycles: compute topological order, rename back-edge targets
    nodes_set, links = _break_sankey_cycles(raw_edges)

    if not links:
        return {}

    nodes = [{"name": n} for n in sorted(nodes_set)]
    return _build_sankey_option(
        f"Transition Flow: {process_config.title}" if process_config.title else "Transition Flow",
        nodes,
        links,
    )


def _break_sankey_cycles(
    edges: list[tuple[str, str, int]],
) -> tuple[set[str], list[dict]]:
    """Break cycles in edges for Sankey DAG requirement.

    Uses DFS to detect back-edges. Back-edges get their target renamed
    to "target (return)" to create a separate node that breaks the cycle
    while preserving the transition information.
    """
    # Build adjacency list
    graph: dict[str, set[str]] = {}
    all_nodes: set[str] = set()
    for src, tgt, _ in edges:
        graph.setdefault(src, set()).add(tgt)
        all_nodes.add(src)
        all_nodes.add(tgt)

    # Compute topological order via DFS (Kahn-like BFS fallback)
    order: dict[str, int] = {}
    visited: set[str] = set()
    temp: set[str] = set()
    back_edges: set[tuple[str, str]] = set()
    counter = [0]

    def dfs(node: str) -> None:
        if node in temp:
            return  # cycle detected, skip
        if node in visited:
            return
        temp.add(node)
        for neighbor in graph.get(node, []):
            if neighbor in temp:
                back_edges.add((node, neighbor))
            elif neighbor not in visited:
                dfs(neighbor)
        temp.discard(node)
        visited.add(node)
        order[node] = counter[0]
        counter[0] += 1

    for node in all_nodes:
        if node not in visited:
            dfs(node)

    # Build links, renaming back-edge targets
    nodes_set: set[str] = set()
    links: list[dict] = []
    for src, tgt, value in edges:
        if (src, tgt) in back_edges:
            renamed = f"{tgt} (return)"
            nodes_set.add(src)
            nodes_set.add(renamed)
            links.append({"source": src, "target": renamed, "value": value})
        else:
            nodes_set.add(src)
            nodes_set.add(tgt)
            links.append({"source": src, "target": tgt, "value": value})

    return nodes_set, links


def _build_sankey_option(title: str, nodes: list[dict], links: list[dict]) -> dict:
    """Build ECharts Sankey option from prepared nodes/links."""
    option = _base_option(title)
    option["tooltip"] = {
        "trigger": "item",
        "triggerOn": "mousemove",
    }
    option["series"] = [{
        "type": "sankey",
        "data": nodes,
        "links": links,
        "emphasis": {"focus": "adjacency"},
        "lineStyle": {"color": "gradient", "curveness": 0.5},
        "label": {"color": "#ccc", "fontSize": 12},
        "itemStyle": {"borderWidth": 1, "borderColor": "#1a1a2e"},
        "nodeGap": 12,
        "layoutIterations": 32,
    }]
    return option


def build_schema_graph_option(
    table_columns: dict[str, list[dict[str, str]]],
    hub_tables: list[dict[str, str]],
    communities: dict[str, int] | None = None,
) -> dict:
    """Build ECharts force-directed graph showing schema table topology.

    Args:
        table_columns: {table_name: [{name, data_type, is_pk, is_fk, fk_ref}]}
        hub_tables: [{name, degree}] — hub tables from graph analysis
        communities: {TABLE_NAME_UPPER: community_id} — from SchemaGraph
    """
    if not table_columns:
        return {}

    communities = communities or {}
    hub_names = {h["name"].upper() for h in hub_tables} if hub_tables else set()

    # Determine number of distinct communities for categories
    community_ids = set(communities.values()) if communities else {0}
    categories = [{"name": f"Domain {i}"} for i in sorted(community_ids)]
    if not categories:
        categories = [{"name": "Domain 0"}]

    nodes = []
    links = []

    for table_name, cols in table_columns.items():
        # Calculate FK degree (outgoing)
        out_degree = sum(1 for c in cols if c.get("is_fk") == "1")
        # Calculate incoming degree (other tables referencing this one)
        in_degree = 0
        for other_name, other_cols in table_columns.items():
            if other_name == table_name:
                continue
            for c in other_cols:
                fk_ref = c.get("fk_ref", "")
                ref_table = fk_ref.split(".")[-1] if fk_ref else ""
                if ref_table and ref_table.upper() == table_name.upper():
                    in_degree += 1

        total_degree = out_degree + in_degree
        is_hub = table_name.upper() in hub_names
        community_id = communities.get(table_name.upper(), 0)

        node: dict = {
            "name": table_name,
            "symbolSize": min(10 + total_degree * 5, 50),
            "category": community_id,
            "value": total_degree,
        }
        if is_hub:
            node["itemStyle"] = {"borderWidth": 3, "borderColor": "#fac858"}
        nodes.append(node)

        # Build edges from FK refs
        for c in cols:
            fk_ref = c.get("fk_ref", "")
            ref_table = fk_ref.split(".")[-1] if fk_ref else ""
            if ref_table:
                links.append({"source": table_name, "target": ref_table})

    option = _base_option("Schema Topology")
    option["tooltip"] = {"trigger": "item"}
    if len(categories) > 1:
        option["legend"] = [
            {"data": [c["name"] for c in categories], "textStyle": {"color": "#ccc"}, "bottom": 0}
        ]
    option["series"] = [{
        "type": "graph",
        "layout": "force",
        "data": nodes,
        "links": links,
        "categories": categories,
        "roam": True,
        "draggable": True,
        "force": {"repulsion": 200, "edgeLength": [50, 150]},
        "label": {"show": True, "color": "#ccc", "fontSize": 10},
        "lineStyle": {"color": "source", "curveness": 0.1, "opacity": 0.6},
        "emphasis": {"focus": "adjacency", "lineStyle": {"width": 3}},
    }]
    return option


def build_timeline_from_event_log(event_log, title: str = "") -> dict:
    """Build ECharts scatter timeline from EventLog with timestamps.

    X axis = time, Y axis = activity, each point = one event.
    Only useful when EventLog has timestamps.
    """
    from biai.models.event_log import EventLog

    if not isinstance(event_log, EventLog) or not event_log.events:
        return {}

    # Filter events with timestamps
    timed_events = [e for e in event_log.events if e.timestamp is not None]
    if not timed_events:
        return {}

    activities = event_log.get_activities()
    activity_idx = {a: i for i, a in enumerate(activities)}

    data_points = []
    for e in timed_events:
        ts = e.timestamp.isoformat() if e.timestamp else ""
        y = activity_idx.get(e.activity, 0)
        data_points.append([ts, y, e.case_id])

    option = _base_option(title or f"Timeline: {event_log.process_id}")
    option["tooltip"] = {
        "trigger": "item",
        "formatter": "{@[2]}: {@[1]}",
    }
    option["xAxis"] = {
        "type": "time",
        "axisLabel": {"color": "#999"},
        "axisLine": {"lineStyle": {"color": "#555"}},
    }
    option["yAxis"] = {
        "type": "category",
        "data": activities,
        "axisLabel": {"color": "#999"},
        "axisLine": {"lineStyle": {"color": "#555"}},
    }
    option["grid"] = {"left": "15%", "right": "5%", "bottom": "15%", "top": "15%"}
    option["series"] = [{
        "type": "scatter",
        "data": data_points,
        "symbolSize": 8,
        "encode": {"x": 0, "y": 1, "tooltip": [0, 2]},
        "itemStyle": {"opacity": 0.7},
    }]
    return option
