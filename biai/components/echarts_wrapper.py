"""ECharts wrapper utilities for dark theme rendering."""

from typing import Any

from biai.models.chart import EChartsOption


# Glow color palette for dark theme
GLOW_COLORS = [
    "#5470c6",
    "#91cc75",
    "#fac858",
    "#ee6666",
    "#73c0de",
    "#3ba272",
    "#fc8452",
    "#9a60b4",
    "#ea7ccc",
]


def build_dark_option(option: dict[str, Any]) -> dict[str, Any]:
    """Apply dark theme defaults and glow effects to an ECharts option."""
    base = EChartsOption.dark_theme_base()

    # Merge base theme
    merged = {**base, **option}

    # Apply color palette
    if "color" not in merged:
        merged["color"] = GLOW_COLORS

    # Apply glow to series
    if "series" in merged:
        for series in merged["series"]:
            if series.get("type") == "bar":
                series.setdefault("itemStyle", {})
                series["itemStyle"].setdefault("borderRadius", [4, 4, 0, 0])
            if series.get("type") == "line":
                series.setdefault("smooth", True)
                series.setdefault("symbolSize", 6)

    # Animation
    merged.setdefault("animation", True)
    merged.setdefault("animationDuration", 800)
    merged.setdefault("animationEasing", "cubicOut")

    return merged
