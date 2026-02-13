"""Process map card - shows discovered processes as interactive grid."""

import reflex as rx

from biai.state.process_map import ProcessMapState, ProcessInfo


def process_map_card() -> rx.Component:
    """Card showing discovered business processes."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("workflow", size=18, color="var(--accent-9)"),
                rx.text("Process Discovery", size="3", weight="bold"),
                rx.spacer(),
                rx.cond(
                    ProcessMapState.is_discovering,
                    rx.spinner(size="2"),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("radar", size=14),
                            variant="outline",
                            size="1",
                            on_click=ProcessMapState.run_discovery,
                        ),
                        content="Discover business processes",
                    ),
                ),
                width="100%",
                align="center",
            ),

            # Error state
            rx.cond(
                ProcessMapState.discovery_error != "",
                rx.callout(
                    ProcessMapState.discovery_error,
                    icon="triangle-alert",
                    color_scheme="orange",
                    size="1",
                ),
            ),

            # Process grid
            rx.cond(
                ProcessMapState.has_processes,
                rx.vstack(
                    rx.text(
                        rx.text.strong(ProcessMapState.process_count),
                        " processes found",
                        size="2",
                        color="var(--gray-10)",
                    ),
                    rx.flex(
                        rx.foreach(
                            ProcessMapState.discovered_processes,
                            _process_card_item,
                        ),
                        wrap="wrap",
                        spacing="3",
                        width="100%",
                    ),
                    width="100%",
                    spacing="3",
                ),
                # Empty state - prompt to discover
                rx.cond(
                    ~ProcessMapState.is_discovering,
                    rx.center(
                        rx.vstack(
                            rx.icon("search", size=28, color="var(--gray-8)", opacity=0.5),
                            rx.text(
                                "Click the radar icon to discover processes",
                                size="2",
                                color="var(--gray-9)",
                            ),
                            align="center",
                            spacing="2",
                        ),
                        padding="16px",
                    ),
                ),
            ),

            width="100%",
            spacing="3",
        ),
        width="100%",
    )


def _process_card_item(process: ProcessInfo) -> rx.Component:
    """Single process card in the grid.

    Note: `process` is a Reflex Var[ProcessInfo] inside rx.foreach.
    Use dot access (process.name) not subscript (process["name"]).
    """
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("git-branch", size=16, color="var(--accent-9)"),
                rx.text(
                    process.name,
                    size="2",
                    weight="bold",
                    trim="both",
                ),
                align="center",
                spacing="2",
            ),
            rx.cond(
                process.description != "",
                rx.text(
                    process.description,
                    size="1",
                    color="var(--gray-10)",
                    trim="both",
                    style={"max_height": "40px", "overflow": "hidden"},
                ),
            ),
            rx.hstack(
                rx.badge(
                    rx.text(
                        process.stages.length(),
                        " stages",
                        size="1",
                    ),
                    variant="surface",
                    size="1",
                ),
                rx.cond(
                    process.confidence >= 0.7,
                    rx.badge("High", color_scheme="green", size="1"),
                    rx.cond(
                        process.confidence >= 0.5,
                        rx.badge("Medium", color_scheme="yellow", size="1"),
                        rx.badge("Low", color_scheme="orange", size="1"),
                    ),
                ),
                spacing="2",
            ),
            spacing="2",
        ),
        style={
            "cursor": "pointer",
            "min_width": "180px",
            "max_width": "260px",
            "flex": "1 1 180px",
            "&:hover": {
                "border_color": "var(--accent-8)",
                "background": "var(--gray-a2)",
            },
        },
        on_click=ProcessMapState.select_process(process.id),
    )
