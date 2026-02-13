"""React Grid Layout NoSSR wrapper for Reflex.

Wraps react-grid-layout as a Reflex NoSSRComponent for drag & drop dashboard.
"""

import reflex as rx
from typing import Any


class ReactGridLayout(rx.NoSSRComponent):
    """react-grid-layout wrapper for dashboard grid."""

    library = "react-grid-layout@1.5.0"
    tag = "GridLayout"
    is_default = True

    layout: rx.Var[list[dict[str, Any]]]
    cols: rx.Var[int] = 12  # type: ignore
    row_height: rx.Var[int] = 80  # type: ignore
    width: rx.Var[int] = 1200  # type: ignore
    is_draggable: rx.Var[bool] = True  # type: ignore
    is_resizable: rx.Var[bool] = True  # type: ignore
    draggable_handle: rx.Var[str] = ".widget-drag-handle"  # type: ignore
    compact_type: rx.Var[str] = "vertical"  # type: ignore
    margin: rx.Var[list[int]] = [12, 12]  # type: ignore

    on_layout_change: rx.EventHandler[lambda layout: [layout]]

    def _get_custom_code(self) -> str:
        return """
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
"""


dashboard_grid = ReactGridLayout.create
