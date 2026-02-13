"""ECharts NoSSR wrapper for Reflex.

Wraps echarts-for-react as a Reflex NoSSRComponent (ECharts requires
client-side rendering). Pattern identical to react_flow/wrapper.py.

Note: Do NOT define a `style` prop — it clashes with Reflex's built-in
Style system. Set dimensions on the wrapping rx.box instead.
"""

import reflex as rx


class EChartsReact(rx.NoSSRComponent):
    """ECharts for React wrapper — renders an Apache ECharts chart."""

    library = "echarts-for-react@3.0.2"
    tag = "ReactECharts"
    is_default = True

    # ECharts option object (the chart specification)
    option: rx.Var[dict]

    # Don't merge with previous option (full replace)
    not_merge: rx.Var[bool] = True  # type: ignore

    # Lazy update (skip animation on data refresh)
    lazy_update: rx.Var[bool] = False  # type: ignore

    lib_dependencies: list[str] = ["echarts@5.6.0"]


echarts_component = EChartsReact.create
