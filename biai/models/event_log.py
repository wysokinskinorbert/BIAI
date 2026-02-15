"""Event log models for process mining analysis."""

from collections import defaultdict
from datetime import datetime

from pydantic import BaseModel, Field


class EventRecord(BaseModel):
    """Single event in a process instance."""

    case_id: str
    activity: str
    timestamp: datetime | None = None
    resource: str = ""
    entity_type: str = ""
    attributes: dict = Field(default_factory=dict)


class EventLog(BaseModel):
    """Collection of events forming a process log.

    Supports transition matrix computation, variant analysis,
    and activity duration calculations for Sankey/Timeline visualizations.
    """

    process_id: str
    events: list[EventRecord] = Field(default_factory=list)
    case_count: int = 0
    activity_count: int = 0

    def get_transition_matrix(self) -> dict[tuple[str, str], int]:
        """Count transitions activity_i -> activity_j per case.

        Returns dict of (from_activity, to_activity) -> count.
        Used for Sankey diagram edge weights.
        """
        transitions: dict[tuple[str, str], int] = defaultdict(int)

        # Group events by case_id, order by timestamp
        cases: dict[str, list[EventRecord]] = defaultdict(list)
        for event in self.events:
            cases[event.case_id].append(event)

        for case_events in cases.values():
            sorted_events = sorted(
                case_events,
                key=lambda e: e.timestamp or datetime.min,
            )
            for i in range(len(sorted_events) - 1):
                pair = (sorted_events[i].activity, sorted_events[i + 1].activity)
                transitions[pair] += 1

        return dict(transitions)

    def get_variant_distribution(self) -> list[tuple[list[str], int]]:
        """Get process variants (unique activity sequences) sorted by frequency.

        Returns list of (activity_sequence, case_count) tuples.
        """
        cases: dict[str, list[EventRecord]] = defaultdict(list)
        for event in self.events:
            cases[event.case_id].append(event)

        variant_counts: dict[tuple[str, ...], int] = defaultdict(int)
        for case_events in cases.values():
            sorted_events = sorted(
                case_events,
                key=lambda e: e.timestamp or datetime.min,
            )
            variant = tuple(e.activity for e in sorted_events)
            variant_counts[variant] += 1

        sorted_variants = sorted(
            variant_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return [(list(v), c) for v, c in sorted_variants]

    def get_activity_durations(self) -> dict[str, float]:
        """Get average time spent per activity (seconds).

        Computed as time between current event and next event in same case.
        Only meaningful when timestamps are present.
        """
        cases: dict[str, list[EventRecord]] = defaultdict(list)
        for event in self.events:
            if event.timestamp is not None:
                cases[event.case_id].append(event)

        durations: dict[str, list[float]] = defaultdict(list)
        for case_events in cases.values():
            sorted_events = sorted(case_events, key=lambda e: e.timestamp)  # type: ignore
            for i in range(len(sorted_events) - 1):
                dt = (sorted_events[i + 1].timestamp - sorted_events[i].timestamp).total_seconds()  # type: ignore
                if dt >= 0:
                    durations[sorted_events[i].activity].append(dt)

        return {
            activity: sum(durs) / len(durs) if durs else 0.0
            for activity, durs in durations.items()
        }

    def get_activities(self) -> list[str]:
        """Get unique activities in order of first appearance."""
        seen: set[str] = set()
        result: list[str] = []
        for event in self.events:
            if event.activity not in seen:
                seen.add(event.activity)
                result.append(event.activity)
        return result
