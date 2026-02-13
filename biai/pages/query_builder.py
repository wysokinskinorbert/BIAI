"""Query Builder page."""

import reflex as rx

from biai.components.query_builder.builder_view import query_builder_view


def builder_page() -> rx.Component:
    """Visual query builder page."""
    return query_builder_view()
