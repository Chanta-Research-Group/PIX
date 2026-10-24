"""Issue #9: hand-calculated uncertainty, ID invariance and persisted evidence."""

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pix.api import (
    ConstraintSpec,
    OCDFGSpec,
    TemporalSpec,
    TimedResponseRule,
    TimePrecision,
    TraceSpec,
    discover_dfg,
    discover_ocdfg,
    evaluate_constraints,
    measure_temporal,
    reconstruct_traces,
    result_from_json,
    result_json_bytes,
)
from pix.ocel import (
    E2O,
    OCEL,
    Attribute,
    Event,
    EventAttr,
    EventType,
    Object,
    ObjectType,
    ValueType,
)

T = datetime(2026, 1, 5, 9, 1, tzinfo=timezone.utc)
MINUTE = TimePrecision(60_000_000)
RULE = ConstraintSpec(
    (TimedResponseRule("ack", "sent", "received", 0, 600_000_000, "first"),), "closed"
)


def log(seconds=0, reverse=False):
    sid, rid = ("b", "a") if reverse else ("a", "b")
    attrs = (Attribute("start", ValueType.TIME),)
    return OCEL(
        (EventType("sent", attrs), EventType("received", attrs)),
        (ObjectType("message"),),
        (
            Event(sid, "sent", T, (EventAttr("start", T - timedelta(minutes=1)),)),
            Event(
                rid,
                "received",
                T + timedelta(seconds=seconds),
                (EventAttr("start", T),),
            ),
        ),
        (Object("m", "message"),),
        (E2O(sid, "m", "sent"), E2O(rid, "m", "received")),
    )


def evaluate(source, precision=MINUTE, rule=RULE):
    traces = reconstruct_traces(
        source, TraceSpec("message", tie_policy="concurrent", time_precision=precision)
    )
    return traces, evaluate_constraints(traces, rule)


@pytest.mark.parametrize("reverse", [False, True])
def test_concurrent_tie_is_indeterminate_regardless_of_event_ids(reverse):
    traces, result = evaluate(log(reverse=reverse))
    assert traces.status.value == result.status.value == "computed"
    row = result.value.rules[0]
    assert (row.fulfilled_count, row.violated_count, row.indeterminate_count) == (
        0,
        0,
        1,
    )
    assert (row.fulfillment_ratio_lower, row.fulfillment_ratio_upper) == (
        (0, 1),
        (1, 1),
    )
    assert row.indeterminate_object_count == 1
    witness = row.traces[0].witnesses[0]
    assert witness.reason == "response_order_unknown_within_precision"
    assert witness.elapsed_microseconds is None
    assert (witness.elapsed_lower_microseconds, witness.elapsed_upper_microseconds) == (
        -60_000_000,
        60_000_000,
    )
    for value in (traces, result):
        assert result_from_json(result_json_bytes(value)) == value


@pytest.mark.parametrize(
    "seconds,state", [(720, "violated"), (120, "fulfilled"), (600, "indeterminate")]
)
def test_window_interval_classification(seconds, state):
    _, result = evaluate(log(seconds))
    assert result.value.rules[0].traces[0].witnesses[0].status == state


def test_exact_precision_and_default_regression():
    source = log(30)
    for precision in (None, TimePrecision(1)):
        _, result = evaluate(source, precision)
        witness = result.value.rules[0].traces[0].witnesses[0]
        assert witness.status == "fulfilled"
        assert witness.elapsed_microseconds == 30_000_000
        temporal = measure_temporal(
            source, TemporalSpec("message", time_precision=precision)
        )
        assert temporal.value.gaps[0].duration.minimum_microseconds == 30_000_000
    a = reconstruct_traces(source, TraceSpec("message"))
    b = reconstruct_traces(source, TraceSpec("message", time_precision=None))
    assert a == b


def test_temporal_interval_bounds_no_point_estimate():
    result = measure_temporal(
        log(reverse=True),
        TemporalSpec(
            "message",
            tie_policy="concurrent",
            time_precision=MINUTE,
            start_attribute="start",
        ),
    )
    duration = result.value.gaps[0].duration
    sample = duration.samples[0]
    assert sample.duration_microseconds is None
    assert (sample.duration_lower_microseconds, sample.duration_upper_microseconds) == (
        0,
        60_000_000,
    )
    assert duration.minimum_microseconds is None
    assert (
        duration.minimum_lower_microseconds,
        duration.maximum_upper_microseconds,
    ) == (0, 60_000_000)
    assert result.value.service_status == "partial"
    assert "service_below_precision" in {i.code for i in result.value.service_issues}
    assert result_from_json(result_json_bytes(result)) == result


def test_precision_mismatch_and_concurrent_dfg_are_rejected():
    traces, _ = evaluate(log())
    result = evaluate_constraints(
        traces, replace(RULE, time_precision=TimePrecision(1))
    )
    assert result.status.value == "invalid_input"
    assert discover_dfg(log(), traces.spec).status.value == "invalid_input"
    assert (
        discover_ocdfg(
            log(), OCDFGSpec(("message",), tie_policy="concurrent")
        ).status.value
        == "invalid_input"
    )


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "60"])
def test_invalid_precision(value):
    with pytest.raises((ValueError, TypeError)):
        TimePrecision(value)


def test_per_event_precision_and_missing_attribute():
    source = log(120)
    source = replace(
        source,
        event_types=tuple(
            replace(t, attributes=t.attributes + (Attribute("g", ValueType.INTEGER),))
            for t in source.event_types
        ),
        events=tuple(
            replace(e, attributes=e.attributes + (EventAttr("g", 60_000_000),))
            for e in source.events
        ),
    )
    _, result = evaluate(source, TimePrecision(attribute="g"))
    assert result.value.rules[0].fulfilled_count == 1
    traces, _ = evaluate(log(), TimePrecision(attribute="g"))
    assert traces.status.value == "invalid_input"


def test_open_observation_without_target_remains_pending():
    source = log()
    source = replace(source, events=source.events[:1], e2o=source.e2o[:1])
    _, result = evaluate(source, rule=replace(RULE, observation_policy="open"))
    assert result.status.value == "partial"
    assert result.value.rules[0].pending_count == 1


def test_same_group_first_and_any_do_not_choose_by_id():
    source = log()
    extra = replace(source.events[1], id="c")
    source = replace(
        source,
        events=source.events + (extra,),
        e2o=source.e2o + (E2O("c", "m", "received"),),
    )
    for selection in ("first", "any"):
        _, result = evaluate(
            source,
            rule=replace(
                RULE, rules=(replace(RULE.rules[0], response_selection=selection),)
            ),
        )
        assert result.value.rules[0].indeterminate_count == 1


def test_time_precision_overflow_is_structured_failure():
    result = reconstruct_traces(
        log(), TraceSpec("message", time_precision=TimePrecision(10**30))
    )
    assert result.status.value == "invalid_input"


def test_prechange_result_documents_and_computation_ids_are_preserved():
    # Generated by unmodified main 71822445, not by the new serializer.
    documents = json.loads(
        (
            Path(__file__).parents[1] / "fixtures/wmc/legacy_results_71822445.json"
        ).read_text()
    )
    source = log(30)
    source = replace(
        source,
        event_types=tuple(replace(t, attributes=()) for t in source.event_types),
        events=tuple(replace(e, attributes=()) for e in source.events),
    )
    trace = reconstruct_traces(source, TraceSpec("message"))
    current = (
        trace,
        evaluate_constraints(trace, RULE),
        measure_temporal(source, TemporalSpec("message")),
    )
    for document, result in zip(documents, current):
        previous = result_from_json(json.dumps(document))
        assert previous == result
        assert previous.computation_id == result.computation_id


def test_tampered_concurrent_groups_are_rejected():
    traces, _ = evaluate(log())
    trace = traces.value.traces[0]
    trace = replace(
        trace, events=(replace(trace.events[0], order_group=9), *trace.events[1:])
    )
    changed = replace(traces, value=replace(traces.value, traces=(trace,)))
    assert evaluate_constraints(changed, RULE).status.value == "invalid_input"


def test_sequential_consumers_reject_concurrent_traces():
    from pix.api import (
        DiscoverySpec,
        PrefixPrecisionSpec,
        align_traces,
        discover_process_tree,
        measure_prefix_precision,
        replay_traces,
    )
    from pix.contracts.models import Marking, PetriNet, Place

    traces, _ = evaluate(log())
    net = PetriNet((Place("p"),), (), (), Marking((("p", 1),)), Marking((("p", 1),)))
    results = (
        discover_process_tree(traces, DiscoverySpec()),
        align_traces(traces, net),
        replay_traces(traces, net),
        measure_prefix_precision(traces, net, PrefixPrecisionSpec("exclude")),
    )
    assert all(result.status.value == "invalid_input" for result in results)
    assert all(
        result.issues[0].code == "concurrent_traces_unsupported" for result in results
    )


def test_uncertain_median_is_an_interval():
    result = measure_temporal(
        log(), TemporalSpec("message", tie_policy="concurrent", time_precision=MINUTE)
    )
    summary = result.value.gaps[0].duration
    assert summary.median_numerator is summary.median_denominator is None
    assert (
        summary.median_lower_numerator,
        summary.median_upper_numerator,
        summary.interval_median_denominator,
    ) == (0, 60_000_000, 1)
    assert "median_indeterminate_within_precision" in {i.code for i in result.issues}
