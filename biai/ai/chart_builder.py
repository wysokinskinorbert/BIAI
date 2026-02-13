"""Build Plotly figure data from ChartConfig and DataFrame."""

import pandas as pd

from biai.models.chart import ChartConfig, ChartType


def build_plotly_figure(chart_config: ChartConfig, df: pd.DataFrame) -> tuple[list[dict], dict]:
    """Build Plotly figure data from ChartConfig and DataFrame.

    Returns (traces, layout) tuple. Empty traces means no chart.
    """
    if chart_config.chart_type == ChartType.TABLE:
        return [], {}

    traces: list[dict] = []

    # --- Special chart types (no x/y requirement) ---

    if chart_config.chart_type == ChartType.HEATMAP:
        traces = _build_heatmap(df)
    elif chart_config.chart_type == ChartType.SANKEY:
        traces = _build_sankey(df)
    elif chart_config.chart_type == ChartType.TIMELINE:
        traces = _build_timeline(chart_config, df)
    else:
        # Standard x/y charts
        x_col = chart_config.x_column
        y_cols = [c for c in chart_config.y_columns if c != x_col]

        if not x_col or not y_cols:
            return [], {}
        if x_col not in df.columns:
            return [], {}

        x_data = df[x_col].astype(str).tolist()

        if chart_config.chart_type == ChartType.PIE:
            if y_cols and y_cols[0] in df.columns:
                traces.append({
                    "type": "pie",
                    "labels": x_data,
                    "values": df[y_cols[0]].tolist(),
                    "hole": 0.4,
                    "textinfo": "label+percent",
                })
        elif chart_config.chart_type == ChartType.SCATTER:
            for y_col in y_cols:
                if y_col in df.columns:
                    traces.append({
                        "type": "scatter",
                        "mode": "markers",
                        "x": x_data,
                        "y": df[y_col].tolist(),
                        "name": y_col,
                    })
        elif chart_config.chart_type == ChartType.AREA:
            for y_col in y_cols:
                if y_col in df.columns:
                    traces.append({
                        "type": "scatter",
                        "mode": "lines",
                        "x": x_data,
                        "y": df[y_col].tolist(),
                        "name": y_col,
                        "fill": "tozeroy",
                    })
        elif chart_config.chart_type == ChartType.LINE:
            for y_col in y_cols:
                if y_col in df.columns:
                    traces.append({
                        "type": "scatter",
                        "mode": "lines+markers",
                        "x": x_data,
                        "y": df[y_col].tolist(),
                        "name": y_col,
                    })
        else:
            # BAR (default)
            for y_col in y_cols:
                if y_col in df.columns:
                    traces.append({
                        "type": "bar",
                        "x": x_data,
                        "y": df[y_col].tolist(),
                        "name": y_col,
                    })

    layout = {
        "title": {"text": chart_config.title},
        "template": "plotly_dark",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#e0e0e0"},
        "margin": {"l": 50, "r": 30, "t": 50, "b": 50},
        "showlegend": len(traces) > 1,
    }

    if chart_config.chart_type not in (ChartType.PIE, ChartType.SANKEY):
        layout["xaxis"] = {"gridcolor": "#333", "linecolor": "#555"}
        layout["yaxis"] = {"gridcolor": "#333", "linecolor": "#555"}

    return traces, layout


def _build_heatmap(df: pd.DataFrame) -> list[dict]:
    """Build heatmap trace from numeric data."""
    numeric_df = df.select_dtypes(include=["number"])
    if numeric_df.empty:
        return []

    z_data = numeric_df.values.tolist()
    x_labels = numeric_df.columns.tolist()
    y_labels = df.index.astype(str).tolist()[:20]

    return [{
        "type": "heatmap",
        "z": z_data[:20],
        "x": x_labels,
        "y": y_labels,
        "colorscale": "Viridis",
        "showscale": True,
    }]


def _build_timeline(chart_config: ChartConfig, df: pd.DataFrame) -> list[dict]:
    """Build timeline trace (scatter with markers+text)."""
    x_col = chart_config.x_column
    y_cols = chart_config.y_columns

    if not x_col or x_col not in df.columns:
        return []

    y_data = (
        df[y_cols[0]].astype(str).tolist()
        if y_cols and y_cols[0] in df.columns
        else list(range(len(df)))
    )
    text_data = (
        df[y_cols[0]].astype(str).tolist()
        if y_cols and y_cols[0] in df.columns
        else []
    )

    return [{
        "type": "scatter",
        "mode": "markers+text",
        "x": df[x_col].astype(str).tolist(),
        "y": y_data,
        "text": text_data,
        "marker": {"size": 12, "color": "#8b5cf6"},
        "textposition": "top center",
    }]


def _build_sankey(df: pd.DataFrame) -> list[dict]:
    """Build sankey trace from source/target/value columns."""
    if len(df.columns) < 3:
        return []

    src_col = df.columns[0]
    tgt_col = df.columns[1]
    val_col = df.columns[2]

    all_labels = list(set(df[src_col].astype(str)) | set(df[tgt_col].astype(str)))
    label_map = {label: i for i, label in enumerate(all_labels)}

    return [{
        "type": "sankey",
        "node": {"label": all_labels, "color": "#8b5cf6"},
        "link": {
            "source": [label_map[s] for s in df[src_col].astype(str)],
            "target": [label_map[t] for t in df[tgt_col].astype(str)],
            "value": df[val_col].tolist(),
        },
    }]
