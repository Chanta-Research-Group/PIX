"""Observed inter-event gaps and explicit event service-time measurements.

These are differences of observed timestamps, not inferred waiting or processing
time. E2O determines the selected object traces. All durations and arithmetic
remain integer microseconds, including the exact mean numerator/denominator.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from itertools import combinations, groupby, product
from typing import Literal

from pix.contracts.analysis import (
    DurationSummary,
    E2OEvidence,
    ObservedTemporal,
    TemporalEdge,
    TemporalIssue,
    TemporalSample,
    TemporalSpec,
    TraceSpec,
    TransitionEvidence,
)
from pix.contracts.result import ComputationResult, ComputeIssue, ComputeStatus
from pix.ocel import OCEL

from ._common import _prepare, _result
from ._time import elapsed, interval, width
from .context import ComputationContext
from .trace import reconstruct_traces

TEMPORAL_OPERATOR_ID = "pix.measure_temporal"

__all__ = ("TEMPORAL_OPERATOR_ID", "measure_temporal")


def _microseconds(delta: timedelta) -> int:
    """Convert exactly, without float timestamps or timedelta.total_seconds()."""

    return (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds


def _median_bound(samples, name):
    values = sorted(getattr(s, name) for s in samples if getattr(s, name) is not None)
    if not values or len(values) != len(samples):
        return None, None
    count = len(values)
    return (
        (values[count // 2], 1)
        if count % 2
        else (values[count // 2 - 1] + values[count // 2], 2)
    )


def _summary(
    samples: tuple[TemporalSample, ...],
    population_count: int,
) -> DurationSummary:
    count = len(samples)
    values = tuple(sample.duration_microseconds for sample in samples)
    exact = all(v is not None for v in values)
    total = sum(values) if exact else None
    median_lower, median_denom = _median_bound(samples, "duration_lower_microseconds")
    median_upper, _ = _median_bound(samples, "duration_upper_microseconds")
    return DurationSummary(
        population_count=population_count,
        sample_count=count,
        unavailable_count=population_count - count,
        total_microseconds=total,
        minimum_microseconds=min(values) if values and exact else None,
        maximum_microseconds=max(values) if values and exact else None,
        mean_numerator=total if values else None,
        mean_denominator=count if values and exact else None,
        samples=samples,
        median_numerator=median_lower
        if median_lower is not None and median_lower == median_upper
        else None,
        median_denominator=median_denom
        if median_lower is not None and median_lower == median_upper
        else None,
        median_lower_numerator=median_lower,
        median_upper_numerator=median_upper,
        interval_median_denominator=median_denom,
        minimum_lower_microseconds=min(s.duration_lower_microseconds for s in samples)
        if samples and all(s.duration_lower_microseconds is not None for s in samples)
        else None,
        minimum_upper_microseconds=min(s.duration_upper_microseconds for s in samples)
        if samples and all(s.duration_upper_microseconds is not None for s in samples)
        else None,
        maximum_lower_microseconds=max(s.duration_lower_microseconds for s in samples)
        if samples and all(s.duration_lower_microseconds is not None for s in samples)
        else None,
        maximum_upper_microseconds=max(s.duration_upper_microseconds for s in samples)
        if samples and all(s.duration_upper_microseconds is not None for s in samples)
        else None,
        mean_lower_numerator=sum(s.duration_lower_microseconds for s in samples)
        if samples and all(s.duration_lower_microseconds is not None for s in samples)
        else None,
        mean_upper_numerator=sum(s.duration_upper_microseconds for s in samples)
        if samples and all(s.duration_upper_microseconds is not None for s in samples)
        else None,
        interval_mean_denominator=count
        if samples and any(s.duration_lower_microseconds is not None for s in samples)
        else None,
    )


def _service(
    context: ComputationContext,
    spec: TemporalSpec,
    selected: dict[str, set[E2OEvidence]],
) -> tuple[
    Literal["computed", "partial", "unavailable"],
    DurationSummary,
    tuple[TemporalIssue, ...],
]:
    """Each selected event is one service sample, independent of object multiplicity."""

    samples: list[TemporalSample] = []
    issues: list[TemporalIssue] = []
    if not selected:
        issues.append(
            TemporalIssue(
                "no_service_events",
                "No events are selected for service measurement",
            )
        )
    elif spec.start_attribute is None:
        issues.append(
            TemporalIssue(
                "service_start_not_selected",
                "Service time is unavailable without an explicit start attribute",
            )
        )
    else:
        for event_id, evidence in sorted(selected.items()):
            event = context.events_by_id[event_id]
            attributes = {item.name: item.value for item in event.attributes}
            start = attributes.get(spec.start_attribute)
            location = ("event", event_id, "attribute", spec.start_attribute)
            if start is None:
                issues.append(
                    TemporalIssue(
                        "missing_service_start",
                        "Selected event has no start attribute",
                        location,
                    )
                )
                continue
            if not isinstance(start, datetime):
                issues.append(
                    TemporalIssue(
                        "invalid_service_start",
                        "Selected start attribute is not a datetime",
                        location,
                    )
                )
                continue
            duration = _microseconds(event.time - start)
            lo = hi = None
            use_interval = spec.time_precision is not None or interval(event, None) != (
                event.time,
                event.time,
            )
            if use_interval:
                span = width(event, spec.time_precision)
                lo, hi = elapsed(
                    (start, start + timedelta(microseconds=span)),
                    interval(event, spec.time_precision),
                )
            if duration < 0 and (not use_interval or (hi is not None and hi < 0)):
                issues.append(
                    TemporalIssue(
                        "negative_service_duration",
                        "Start attribute is later than the event timestamp",
                        location,
                    )
                )
                continue
            if use_interval:
                if (
                    lo is None
                    or hi is None
                    or hi - lo >= 2 * max(1, width(event, spec.time_precision))
                ):
                    issues.append(
                        TemporalIssue(
                            "service_below_precision",
                            "Service duration is bounded only by observation precision",
                            location,
                        )
                    )
                lo = max(0, lo) if lo is not None else 0
                duration = lo if lo == hi else None
            relations = tuple(
                sorted(
                    evidence,
                    key=lambda item: (item.event, item.object, item.qualifier),
                )
            )
            samples.append(
                TemporalSample(
                    source_event_id=None,
                    target_event_id=event_id,
                    object_ids=tuple(sorted({item.object for item in relations})),
                    duration_microseconds=duration,
                    relations=relations,
                    duration_lower_microseconds=lo,
                    duration_upper_microseconds=hi,
                )
            )
    return (
        (
            "partial"
            if samples
            and any(s.duration_lower_microseconds is not None for s in samples)
            else "unavailable"
        )
        if issues
        else "computed",
        _summary(tuple(samples), len(selected)),
        tuple(issues),
    )


def measure_temporal(
    log: OCEL | ComputationContext,
    spec: TemporalSpec,
) -> ComputationResult[ObservedTemporal]:
    """Measure selected trace gaps and coverage of explicitly recorded service times.

    ``weighting='event_pairs'`` gives one gap sample per unique event pair;
    ``'occurrences'`` gives one per object/event-pair occurrence. Both retain all
    contributing evidence. Service measurements always use unique selected events
    and require a datetime attribute named by ``start_attribute``. Missing, invalid,
    or negative service durations remain unavailable, with measured subset and
    coverage retained; this does not invalidate independently measured gaps. When
    an explicitly requested start attribute cannot measure every selected event,
    the envelope is partial. Without a start selection only gaps are requested.

    Equal timestamps are ambiguous unless the caller explicitly selects lexical
    event-id ordering. Such an explicit ordering can yield an observed zero gap;
    it does not establish causal succession. Empty input is not assigned a zero
    mean: min/max/mean fields remain None wherever no samples exist.
    """

    if not isinstance(spec, TemporalSpec):
        raise TypeError("spec must be TemporalSpec")
    context, issues = _prepare(log)
    if context is None:
        return _result(
            TEMPORAL_OPERATOR_ID,
            None,
            spec,
            ComputeStatus.INVALID_INPUT,
            None,
            issues,
        )
    trace_result = reconstruct_traces(
        context,
        TraceSpec(
            spec.object_type, spec.qualifiers, spec.tie_policy, spec.time_precision
        ),
    )
    parent_ids = (
        (trace_result.computation_id,)
        if trace_result.computation_id is not None
        else ()
    )
    if trace_result.status is not ComputeStatus.COMPUTED:
        return _result(
            TEMPORAL_OPERATOR_ID,
            context,
            spec,
            trace_result.status,
            None,
            trace_result.issues,
            parent_computation_ids=parent_ids,
        )
    assert trace_result.value is not None
    selected: dict[str, set[E2OEvidence]] = defaultdict(set)
    pairs: dict[tuple[str, str], list[TransitionEvidence]] = defaultdict(list)
    unordered_pairs = set()
    concurrent_pair_count = 0
    for trace in trace_result.value.traces:
        for event in trace.events:
            selected[event.event_id].update(event.relations)
        if spec.tie_policy == "concurrent":
            groups = [
                tuple(items)
                for _, items in groupby(trace.events, key=lambda e: e.order_group)
            ]
            concurrent_pair_count += sum(
                len(g) * (len(g) - 1) // 2 for g in groups
            ) + sum(len(a) * len(b) for a, b in zip(groups, groups[1:]))
            if concurrent_pair_count > 100_000:
                return _result(
                    TEMPORAL_OPERATOR_ID,
                    context,
                    spec,
                    ComputeStatus.UNAVAILABLE,
                    None,
                    (
                        ComputeIssue(
                            "concurrent_temporal_pair_limit",
                            "Concurrent temporal measurement exceeds 100000 possible pair occurrences; narrow the object/qualifier selection",
                        ),
                    ),
                    parent_computation_ids=parent_ids,
                )
            candidates = []
            for group in groups:
                for source, target in combinations(
                    sorted(group, key=lambda e: (e.activity, e.event_id)), 2
                ):
                    candidates.append((source, target))
                    unordered_pairs.add((source.event_id, target.event_id))
            for before, after in zip(groups, groups[1:]):
                candidates.extend(product(before, after))
        else:
            candidates = zip(trace.events, trace.events[1:])
        for source, target in candidates:
            pairs[source.event_id, target.event_id].append(
                TransitionEvidence(
                    object_id=trace.object_id,
                    source_event_id=source.event_id,
                    target_event_id=target.event_id,
                    source_relations=source.relations,
                    target_relations=target.relations,
                )
            )

    edge_samples: dict[tuple[str, str], list[TemporalSample]] = defaultdict(list)
    for (source_id, target_id), records in sorted(pairs.items()):
        source, target = (
            context.events_by_id[source_id],
            context.events_by_id[target_id],
        )
        duration = _microseconds(target.time - source.time)
        lo = hi = None
        if (
            spec.time_precision is not None
            or spec.tie_policy == "concurrent"
            or interval(source, None) != (source.time, source.time)
            or interval(target, None) != (target.time, target.time)
        ):
            lo, hi = elapsed(
                interval(source, spec.time_precision),
                interval(target, spec.time_precision),
            )
            if (source_id, target_id) in unordered_pairs:
                # This is an unordered separation, not a directed causal gap.
                hi = (
                    max(abs(lo), abs(hi)) if lo is not None and hi is not None else None
                )
                lo = 0
            elif lo is not None:
                lo = max(0, lo)
            duration = lo if lo is not None and lo == hi else None
        if duration is not None and duration < 0:
            return _result(
                TEMPORAL_OPERATOR_ID,
                context,
                spec,
                ComputeStatus.UNAVAILABLE,
                None,
                (
                    ComputeIssue(
                        "negative_event_gap",
                        "Target precedes source in an observed trace",
                        ("events", source_id, target_id),
                    ),
                ),
                parent_computation_ids=parent_ids,
            )
        ordered_records = tuple(sorted(records, key=lambda item: item.object_id))
        groups = (
            (ordered_records,)
            if spec.weighting == "event_pairs"
            else tuple((record,) for record in ordered_records)
        )
        for evidence in groups:
            edge_samples[source.type, target.type].append(
                TemporalSample(
                    source_event_id=source_id,
                    target_event_id=target_id,
                    object_ids=tuple(item.object_id for item in evidence),
                    duration_microseconds=duration,
                    evidence=evidence,
                    duration_lower_microseconds=lo,
                    duration_upper_microseconds=hi,
                )
            )

    gaps = tuple(
        TemporalEdge(
            source_activity=source,
            target_activity=target,
            duration=_summary(tuple(samples), len(samples)),
        )
        for (source, target), samples in sorted(edge_samples.items())
    )
    service_status, service, service_issues = _service(context, spec, selected)
    status = (
        ComputeStatus.PARTIAL
        if spec.start_attribute is not None and service_issues
        else ComputeStatus.COMPUTED
    )
    interval_issues = ()
    if unordered_pairs:
        interval_issues = (
            ComputeIssue(
                "unordered_temporal_pairs",
                "Within-group pairs are unordered separations; adjacent-group pairs are possible successions, not asserted directly-follows",
            ),
        )
    if any(
        summary.median_lower_numerator is not None and summary.median_numerator is None
        for summary in (*[edge.duration for edge in gaps], service)
    ):
        interval_issues += (
            ComputeIssue(
                "median_indeterminate_within_precision",
                "Only median bounds are known; no point median is reported",
            ),
        )
    return _result(
        TEMPORAL_OPERATOR_ID,
        context,
        spec,
        status,
        ObservedTemporal(
            object_type=spec.object_type,
            weighting=spec.weighting,
            gaps=gaps,
            service_status=service_status,
            service=service,
            service_issues=service_issues,
        ),
        interval_issues
        + tuple(
            ComputeIssue(issue.code, issue.message, issue.at)
            for issue in service_issues
        ),
        parent_computation_ids=parent_ids,
    )
