"""Dashboard Builder page component — full-width grid with widget palette."""

import reflex as rx

from biai.state.dashboard import DashboardState, DASHBOARD_TEMPLATES
from biai.components.dashboard_builder.grid_layout import dashboard_grid
from biai.components.dashboard_builder.widget import dashboard_widget


def dashboard_builder_page() -> rx.Component:
    """Full dashboard builder view."""
    return rx.vstack(
        # Top toolbar
        _toolbar(),

        # Main content
        rx.hstack(
            # Widget palette (collapsible sidebar)
            rx.cond(
                DashboardState.show_widget_palette,
                _widget_palette(),
            ),

            # Grid area
            rx.box(
                rx.cond(
                    DashboardState.has_widgets,
                    rx.box(
                        dashboard_grid(
                            rx.foreach(
                                DashboardState.widgets,
                                dashboard_widget,
                            ),
                            layout=DashboardState.layout,
                            cols=12,
                            row_height=80,
                            is_draggable=DashboardState.is_edit_mode,
                            is_resizable=DashboardState.is_edit_mode,
                            on_layout_change=DashboardState.on_layout_change,
                        ),
                        width="100%",
                        min_height="calc(100vh - 60px)",
                    ),
                    _empty_grid(),
                ),
                flex="1",
                overflow_y="auto",
                padding="16px",
            ),
            width="100%",
            flex="1",
            spacing="0",
        ),

        # Save dialog
        rx.cond(
            DashboardState.show_save_dialog,
            _save_dialog(),
        ),

        # Widget edit dialog
        rx.cond(
            DashboardState.is_editing,
            _edit_widget_dialog(),
        ),

        # Template picker dialog
        rx.cond(
            DashboardState.show_template_picker,
            _template_picker_dialog(),
        ),

        width="100%",
        height="100vh",
        spacing="0",
        bg="var(--color-background)",
    )


def _toolbar() -> rx.Component:
    """Dashboard toolbar with actions."""
    return rx.hstack(
        rx.hstack(
            rx.icon("layout-dashboard", size=20, color="var(--accent-9)"),
            rx.text(DashboardState.dashboard_name, size="4", weight="bold"),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        # Widget palette toggle
        rx.tooltip(
            rx.button(
                rx.icon("plus", size=14),
                "Add Widget",
                variant=rx.cond(DashboardState.show_widget_palette, "soft", "outline"),
                size="1",
                on_click=DashboardState.toggle_widget_palette,
            ),
            content="Toggle widget palette",
        ),
        # Edit mode toggle
        rx.tooltip(
            rx.button(
                rx.icon(
                    rx.cond(DashboardState.is_edit_mode, "lock-open", "lock"),
                    size=14,
                ),
                rx.cond(DashboardState.is_edit_mode, "Editing", "Locked"),
                variant="outline",
                size="1",
                on_click=DashboardState.toggle_edit_mode,
            ),
            content="Toggle edit/lock mode",
        ),
        # Save
        rx.button(
            rx.icon("save", size=14),
            "Save",
            variant="outline",
            size="1",
            on_click=DashboardState.set_show_save_dialog(True),
        ),
        # Set as Default (only when dashboard has widgets)
        rx.cond(
            DashboardState.has_widgets,
            rx.tooltip(
                rx.button(
                    rx.icon("home", size=14),
                    "Set Default",
                    variant="outline",
                    size="1",
                    on_click=DashboardState.set_as_default,
                ),
                content="Show this dashboard on the main page",
            ),
        ),
        # Load saved
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.icon("folder-open", size=14),
                    "Load",
                    variant="outline",
                    size="1",
                    on_click=DashboardState.refresh_saved_list,
                ),
            ),
            rx.menu.content(
                rx.cond(
                    DashboardState.saved_dashboards.length() > 0,
                    rx.foreach(
                        DashboardState.saved_dashboards,
                        lambda d: rx.menu.item(
                            d["name"],
                            on_click=DashboardState.load_dashboard(d["file"]),
                        ),
                    ),
                    rx.menu.item("No saved dashboards", disabled=True),
                ),
            ),
        ),
        # Templates
        rx.button(
            rx.icon("layout-template", size=14),
            "Templates",
            variant="outline",
            size="1",
            on_click=DashboardState.set_show_template_picker(True),
        ),
        # Back to main
        rx.link(
            rx.button(
                rx.icon("arrow-left", size=14),
                "Back",
                variant="ghost",
                size="1",
            ),
            href="/",
        ),
        width="100%",
        align="center",
        padding="8px 16px",
        border_bottom="1px solid var(--gray-a5)",
        bg="var(--color-panel)",
        spacing="2",
    )


def _widget_palette() -> rx.Component:
    """Sidebar palette for adding widgets."""
    return rx.vstack(
        rx.text("Add Widget", size="2", weight="bold"),
        _palette_item("chart", "bar-chart-3", "Chart", "Add a visualization"),
        _palette_item("kpi", "hash", "KPI", "Big number metric"),
        _palette_item("table", "table-2", "Table", "Data table view"),
        _palette_item("text", "type", "Text", "Notes or description"),
        _palette_item("insight", "lightbulb", "Insight", "AI-generated insight"),
        width="200px",
        min_width="200px",
        padding="12px",
        border_right="1px solid var(--gray-a5)",
        spacing="2",
        height="calc(100vh - 60px)",
        bg="var(--color-panel)",
    )


def _palette_item(widget_type: str, icon_name: str, label: str, desc: str) -> rx.Component:
    """Single item in widget palette."""
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=16, color="var(--accent-9)"),
            rx.vstack(
                rx.text(label, size="2", weight="medium"),
                rx.text(desc, size="1", color="var(--gray-9)"),
                spacing="0",
            ),
            spacing="2",
            align="center",
        ),
        variant="ghost",
        width="100%",
        on_click=DashboardState.add_widget(widget_type),
    )


def _empty_grid() -> rx.Component:
    """Empty dashboard state."""
    return rx.center(
        rx.vstack(
            rx.icon("layout-dashboard", size=48, color="var(--gray-8)", opacity=0.4),
            rx.text("Empty Dashboard", size="3", color="var(--gray-10)"),
            rx.text(
                "Click 'Add Widget' to start building your dashboard",
                size="2",
                color="var(--gray-9)",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("plus", size=14),
                    "Add Widget",
                    on_click=DashboardState.toggle_widget_palette,
                ),
                rx.button(
                    rx.icon("layout-template", size=14),
                    "From Template",
                    variant="outline",
                    on_click=DashboardState.set_show_template_picker(True),
                ),
                spacing="2",
                margin_top="8px",
            ),
            align="center",
            spacing="2",
        ),
        width="100%",
        height="calc(100vh - 60px)",
    )


def _save_dialog() -> rx.Component:
    """Save dashboard dialog."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Save Dashboard"),
            rx.vstack(
                rx.text("Dashboard name:", size="2"),
                rx.input(
                    placeholder="My Dashboard",
                    value=DashboardState.save_name,
                    on_change=DashboardState.set_save_name,
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Cancel", variant="outline", size="2"),
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Save",
                            size="2",
                            on_click=DashboardState.save_dashboard,
                        ),
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
            ),
        ),
        open=DashboardState.show_save_dialog,
        on_open_change=DashboardState.set_show_save_dialog,
    )


def _edit_widget_dialog() -> rx.Component:
    """Dialog for editing a widget's configuration."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Edit Widget"),
            rx.vstack(
                # Title (common for all types)
                rx.text("Title:", size="2", weight="medium"),
                rx.input(
                    value=DashboardState.edit_title,
                    on_change=DashboardState.set_edit_title,
                    width="100%",
                ),

                # Type-specific fields
                # Text widget: content
                rx.cond(
                    DashboardState.editing_widget_type == "text",
                    rx.vstack(
                        rx.text("Content (Markdown):", size="2", weight="medium"),
                        rx.text_area(
                            value=DashboardState.edit_content,
                            on_change=DashboardState.set_edit_content,
                            width="100%",
                            rows="6",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                ),

                # KPI widget: value + label
                rx.cond(
                    DashboardState.editing_widget_type == "kpi",
                    rx.vstack(
                        rx.text("Value:", size="2", weight="medium"),
                        rx.input(
                            value=DashboardState.edit_kpi_value,
                            on_change=DashboardState.set_edit_kpi_value,
                            width="100%",
                        ),
                        rx.text("Label:", size="2", weight="medium"),
                        rx.input(
                            value=DashboardState.edit_kpi_label,
                            on_change=DashboardState.set_edit_kpi_label,
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                ),

                # Insight widget: title + description
                rx.cond(
                    DashboardState.editing_widget_type == "insight",
                    rx.vstack(
                        rx.text("Insight Title:", size="2", weight="medium"),
                        rx.input(
                            value=DashboardState.edit_insight_title,
                            on_change=DashboardState.set_edit_insight_title,
                            width="100%",
                        ),
                        rx.text("Description:", size="2", weight="medium"),
                        rx.text_area(
                            value=DashboardState.edit_insight_description,
                            on_change=DashboardState.set_edit_insight_description,
                            width="100%",
                            rows="4",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                ),

                # Chart widget: info only (chart data comes from queries)
                rx.cond(
                    DashboardState.editing_widget_type == "chart",
                    rx.callout(
                        "Chart data is populated from query results. "
                        "Use 'Add to Dashboard' from the main view.",
                        icon="info",
                        size="1",
                    ),
                ),

                # Action buttons
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        size="2",
                        on_click=DashboardState.cancel_edit_widget,
                    ),
                    rx.button(
                        "Save",
                        size="2",
                        on_click=DashboardState.save_widget_edit,
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="480px",
        ),
        open=DashboardState.is_editing,
        on_open_change=lambda v: DashboardState.cancel_edit_widget(),
    )


def _template_picker_dialog() -> rx.Component:
    """Dialog for selecting a dashboard template."""
    template_cards = []
    for idx, tpl in enumerate(DASHBOARD_TEMPLATES):
        is_first = idx == 0
        template_cards.append(
            rx.dialog.close(
                rx.button(
                    rx.hstack(
                        rx.icon(tpl["icon"], size=20, color="var(--accent-9)"),
                        rx.vstack(
                            rx.hstack(
                                rx.text(tpl["name"], size="2", weight="bold"),
                                *(
                                    [rx.badge("Recommended", size="1", variant="solid", color_scheme="violet")]
                                    if is_first
                                    else []
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.text(tpl["description"], size="1", color="var(--gray-10)"),
                            rx.text(
                                f"{len(tpl['widgets'])} widgets",
                                size="1",
                                color="var(--gray-9)",
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    variant="soft" if is_first else "outline",
                    width="100%",
                    height="auto",
                    padding="12px 16px",
                    on_click=DashboardState.load_template(idx),
                ),
            )
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("New from Template"),
            rx.dialog.description(
                "Choose a template to start with. You can customize it later.",
                size="2",
            ),
            rx.vstack(
                *template_cards,
                rx.separator(),
                rx.dialog.close(
                    rx.button("Cancel", variant="outline", size="2", width="100%"),
                ),
                spacing="3",
                width="100%",
                padding_top="12px",
            ),
            max_width="480px",
        ),
        open=DashboardState.show_template_picker,
        on_open_change=DashboardState.set_show_template_picker,
    )
