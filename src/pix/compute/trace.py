"""Native per-object traces with explicit ordering and qualified E2O evidence."""

from __future__ import annotations

from collections import defaultdict

from pix.compute._common import OPERATOR_VERSION, _prepare, _result
from pix.compute._time import interval
from pix.compute.context import ComputationContext
from pix.contracts.analysis import (
    E2OEvidence,
    ObjectTrace,
    TraceEvent,
    TraceSet,
    TraceSpec,
)
from pix.contracts.result import ComputationResult, ComputeIssue, ComputeStatus
from pix.ocel import OCEL

TRACE_OPERATOR_ID = "pix.reconstruct_traces"


def _traces(
    context: ComputationContext,
    spec: TraceSpec,
) -> tuple[TraceSet | None, tuple[ComputeIssue, ...]]:
    if spec.object_type not in context.objects_by_type:
        return None, (
            ComputeIssue(
                "unknown_object_type",
                f"Object type {spec.object_type!r} is not declared in this OCEL",
                ("object_type", spec.object_type),
            ),
        )

    allowed = None if spec.qualifiers is None else frozenset(spec.qualifiers)
    traces: list[ObjectTrace] = []
    issues: list[ComputeIssue] = []
    for obj in context.objects_by_type[spec.object_type]:
        by_event: dict[str, list[E2OEvidence]] = defaultdict(list)
        for relation in context.e2o_by_object[obj.id]:
            if allowed is None or relation.qualifier in allowed:
                by_event[relation.event].append(
                    E2OEvidence(relation.event, relation.object, relation.qualifier)
                )
        events = sorted(
            (context.events_by_id[event_id] for event_id in by_event),
            key=lambda event: (event.time, event.id),
        )
        bounds = {}
        groups = {}
        group = -1
        right = None
        previous_lower = None
        try:
            for event in events:
                lower, upper = interval(event, spec.time_precision)
                bounds[event.id] = lower, upper
                overlaps = group >= 0 and (
                    right is None or lower < right or lower == previous_lower
                )
                if not overlaps:
                    group += 1
                    right = upper
                elif right is not None:
                    right = None if upper is None else max(right, upper)
                groups[event.id] = group
                previous_lower = lower
        except (ValueError, TypeError, OverflowError) as exc:
            return None, (
                ComputeIssue("invalid_time_precision", str(exc), ("object", obj.id)),
            )
        for previous, following in zip(events, events[1:]):
            if groups[previous.id] == groups[following.id]:
                if spec.tie_policy == "concurrent":
                    issues.append(
                        ComputeIssue(
                            "concurrent_event_order",
                            "Overlapping observations have no asserted internal order",
                            ("object", obj.id, "events", previous.id, following.id),
                        )
                    )
                    continue
                if spec.tie_policy == "reject":
                    issues.append(
                        ComputeIssue(
                            "ambiguous_event_order",
                            "Equal timestamps within this object's selected events; "
                            "choose an explicit tie policy to compute a sequence",
                            ("object", obj.id, "events", previous.id, following.id),
                        )
                    )
                else:
                    issues.append(
                        ComputeIssue(
                            "timestamp_tie_broken",
                            "Equal timestamps were ordered by event ID under the "
                            "explicit event_id policy; this is not causal evidence",
                            ("object", obj.id, "events", previous.id, following.id),
                        )
                    )
        traces.append(
            ObjectTrace(
                obj.id,
                obj.type,
                tuple(
                    TraceEvent(
                        event.id,
                        event.type,
                        event.time,
                        tuple(by_event[event.id]),
                        groups[event.id] if spec.tie_policy == "concurrent" else None,
                        bounds[event.id][0]
                        if spec.time_precision is not None
                        or bounds[event.id] != (event.time, event.time)
                        else None,
                        bounds[event.id][1]
                        if spec.time_precision is not None
                        or bounds[event.id] != (event.time, event.time)
                        else None,
                    )
                    for event in events
                ),
            )
        )
    if any(issue.code == "ambiguous_event_order" for issue in issues):
        return None, tuple(issues)
    return TraceSet(spec.object_type, tuple(traces)), tuple(issues)


def reconstruct_traces(
    log: OCEL | ComputationContext,
    spec: TraceSpec,
) -> ComputationResult[TraceSet]:
    """Compute one E2O trace per selected object, including isolated objects.

    Multiple qualifying E2O records produce one event occurrence with all matching
    relation evidence. Unknown object types and ambiguous selected-object ordering
    are unavailable; invalid OCEL is invalid_input. No partial success is returned.
    """

    if not isinstance(spec, TraceSpec):
        raise TypeError("spec must be TraceSpec")
    context, issues = _prepare(log)
    if context is None:
        return _result(
            TRACE_OPERATOR_ID, None, spec, ComputeStatus.INVALID_INPUT, None, issues
        )
    traces, issues = _traces(context, spec)
    return _result(
        TRACE_OPERATOR_ID,
        context,
        spec,
        ComputeStatus.COMPUTED
        if traces is not None
        else (
            ComputeStatus.INVALID_INPUT
            if any(i.code == "invalid_time_precision" for i in issues)
            else ComputeStatus.UNAVAILABLE
        ),
        traces,
        issues,
    )


__all__ = ("OPERATOR_VERSION", "TRACE_OPERATOR_ID", "reconstruct_traces")
