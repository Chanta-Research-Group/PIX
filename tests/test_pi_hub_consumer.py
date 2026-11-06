"""Neutral consumer acceptance: hand-derived expectations, public APIs only."""

import copy
import json
import runpy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pix.api import (
    CarrierRule,
    ChatLogMapping,
    ConstraintSpec,
    ExecutionSpec,
    HandoverSpec,
    MatchRule,
    OCDFGSpec,
    TemporalSpec,
    TimedResponseRule,
    TimePrecision,
    TraceSpec,
    VariantSpec,
    discover_executions,
    discover_handover,
    discover_ocdfg,
    discover_variants,
    evaluate_constraints,
    import_chat_log,
    measure_temporal,
    read_result,
    reconstruct_traces,
    result_from_json,
    result_json_bytes,
)
from pix.ocel import (
    E2O,
    Attribute,
    EventAttr,
    Object,
    ObjectAttr,
    ValueType,
    canonical_digest,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pi_hub"
EXAMPLE = runpy.run_path(str(ROOT / "examples/adapter_contract_demo.py"))
MAPPING = json.loads((FIXTURE / "mapping.json").read_bytes())
DOCUMENT = json.loads((FIXTURE / "normalized.json").read_bytes())
MINUTE = TimePrecision(60_000_000)
RULE = ConstraintSpec(
    (TimedResponseRule("ack", "sent", "received", 0, 600_000_000, "first"),), "closed"
)


def snapshot(document=None, mapping=None):
    built = EXAMPLE["build_snapshot"](document or DOCUMENT, mapping or MAPPING)
    assert built.valid, built.report
    return built.ocel


def pair(seconds=0, reverse_ids=False):
    doc = copy.deepcopy(DOCUMENT)
    doc["events"] = doc["events"][-2:]
    sent, received = doc["events"]
    sent["id"], received["id"] = ("z", "a") if reverse_ids else ("a", "z")
    received["occurred_at"] = (
        datetime.fromisoformat(sent["occurred_at"]) + timedelta(seconds=seconds)
    ).isoformat()
    return snapshot(doc)


def evaluate(log, precision=MINUTE, rule=RULE):
    traces = reconstruct_traces(
        log, TraceSpec("message", tie_policy="concurrent", time_precision=precision)
    )
    return traces, evaluate_constraints(traces, rule)


def anchor(log, *, upper_seconds):
    target = next(e for e in log.events if e.type == "received")
    attrs = [
        EventAttr("time_basis", "anchor_previous_observed"),
        EventAttr("time_lower", target.time),
    ]
    declarations = [
        Attribute("time_basis", ValueType.STRING),
        Attribute("time_lower", ValueType.TIME),
    ]
    if upper_seconds is not None:
        attrs.append(
            EventAttr("time_upper", target.time + timedelta(seconds=upper_seconds))
        )
        declarations.append(Attribute("time_upper", ValueType.TIME))
    return replace(
        log,
        events=tuple(
            replace(e, attributes=e.attributes + tuple(attrs))
            if e.id == target.id
            else e
            for e in log.events
        ),
        event_types=tuple(
            replace(t, attributes=t.attributes + tuple(declarations))
            if t.name == target.type
            else t
            for t in log.event_types
        ),
    )


def test_f01_f02_f09_bundle_roundtrip_parent_closure_and_reproducibility(tmp_path):
    records = [EXAMPLE["run"](FIXTURE, tmp_path / name) for name in ("first", "second")]
    assert records[0] == records[1]
    assert records[0]["coverage"]["excluded_events"] == 0
    for item in records[0]["results"].values():
        result = read_result(tmp_path / "first" / item["artifact"])
        assert result.source_digest == records[0]["source_digest"]
        parents = [
            read_result(tmp_path / "first" / name) for name in item["parent_artifacts"]
        ]
        assert tuple(p.computation_id for p in parents) == result.parent_computation_ids
    assert records[0]["results"]["constraints"]["parent_artifacts"] == [
        "traces.result.json"
    ]
    assert records[0]["results"]["variants"]["parent_artifacts"] == [
        "executions.result.json"
    ]
    assert records[0]["results"]["ocdfg"]["parent_artifacts"] == [
        "task_dfg.result.json"
    ]


def test_f01_manual_expected_values_are_enforced(tmp_path):
    fixture = tmp_path / "bad-fixture"
    fixture.mkdir()
    for path in FIXTURE.glob("*.json"):
        (fixture / path.name).write_bytes(path.read_bytes())
    expected = json.loads((fixture / "expected.json").read_bytes())
    expected["event_count"] = 999
    (fixture / "expected.json").write_text(json.dumps(expected))
    with pytest.raises(RuntimeError, match="Hand-calculated"):
        EXAMPLE["run"](fixture, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_f02_source_ids_mapping_timezone_and_input_order():
    source = snapshot()
    doc = copy.deepcopy(DOCUMENT)
    doc["objects"].reverse()
    doc["events"].reverse()
    for row in doc["events"]:
        row["occurred_at"] = (
            datetime.fromisoformat(row["occurred_at"])
            .astimezone(timezone.utc)
            .isoformat()
        )
        row["relationships"].reverse()
    assert canonical_digest(snapshot(doc)) == canonical_digest(source)
    changed = snapshot(mapping={**MAPPING, "id_namespace": "other"})
    assert canonical_digest(changed) != canonical_digest(source)
    for event in source.events:
        attrs = {a.name: a.value for a in event.attributes}
        assert attrs["source_id"] == "synthetic"
        assert attrs["source_event_id"] in {e["id"] for e in DOCUMENT["events"]}
        assert attrs["mapping_digest"] == EXAMPLE["mapping_digest"](MAPPING)


@pytest.mark.parametrize(
    "kind", ["missing_object", "missing_event", "missing_o2o", "duplicate_object"]
)
def test_f02_broken_references_are_diagnosed(kind):
    log = snapshot()
    if kind == "missing_object":
        log = replace(log, e2o=log.e2o + (E2O(log.events[0].id, "absent", "task"),))
    elif kind == "missing_event":
        log = replace(log, e2o=log.e2o + (E2O("absent", "task:1", "task"),))
    elif kind == "missing_o2o":
        log = replace(log, o2o=(replace(log.o2o[0], target="absent"),))
    else:
        log = replace(log, objects=log.objects + (log.objects[0],))
    report = validate(log)
    assert not report.valid and report.errors
    result = reconstruct_traces(log, TraceSpec("task"))
    assert result.status.value == "invalid_input" and result.value is None


@pytest.mark.parametrize("timestamp", [None, "2026-01-05T09:00:00"])
def test_f02_f04_unobserved_or_naive_time_is_not_invented(timestamp):
    doc = copy.deepcopy(DOCUMENT)
    doc["events"][0]["occurred_at"] = timestamp
    with pytest.raises((RuntimeError, ValueError)):
        EXAMPLE["build_snapshot"](doc, MAPPING)


@pytest.mark.parametrize(
    "seconds,status,bounds",
    [
        (0, "indeterminate", (-60_000_000, 60_000_000)),
        (600, "indeterminate", (540_000_000, 660_000_000)),
        (720, "violated", (660_000_000, 780_000_000)),
        (120, "fulfilled", (60_000_000, 180_000_000)),
    ],
)
def test_f03_f04_interval_semantics_survive_id_renaming(seconds, status, bounds):
    identities = []
    for reverse in (False, True):
        log = pair(seconds, reverse)
        traces, result = evaluate(log)
        witness = result.value.rules[0].traces[0].witnesses[0]
        assert witness.status == status
        assert (
            witness.elapsed_lower_microseconds,
            witness.elapsed_upper_microseconds,
        ) == bounds
        identities.append(result.computation_id)
        handover = discover_handover(
            log, HandoverSpec(actor_object_type="agent", time_precision=MINUTE)
        )
        assert len(handover.value.links) == 1
        assert not handover.value.order_conflicts
        for value in (traces, result, handover):
            assert result_from_json(result_json_bytes(value)) == value
    assert (
        identities[0] != identities[1]
    )  # IDs are canonical facts, semantics are invariant.


def test_f03_exact_point_and_second_bucket_are_different():
    log = pair(30)
    _, exact = evaluate(log, precision=None)
    _, bucket = evaluate(log, precision=TimePrecision(1_000_000))
    a, b = (r.value.rules[0].traces[0].witnesses[0] for r in (exact, bucket))
    assert a.elapsed_microseconds == 30_000_000
    assert b.elapsed_microseconds is None
    assert (b.elapsed_lower_microseconds, b.elapsed_upper_microseconds) == (
        29_000_000,
        31_000_000,
    )


@pytest.mark.parametrize("upper", [30, None])
def test_f04_external_anchor_uses_existing_contract(upper):
    log = anchor(pair(120), upper_seconds=upper)
    traces, result = evaluate(log, precision=None)
    witness = result.value.rules[0].traces[0].witnesses[0]
    assert witness.elapsed_lower_microseconds == 120_000_000
    assert witness.elapsed_upper_microseconds == (150_000_000 if upper else None)
    assert witness.status == ("fulfilled" if upper else "indeterminate")
    assert result_from_json(result_json_bytes(traces)) == traces
    assert result_from_json(result_json_bytes(result)) == result


def test_f04_invalid_anchor_and_open_closed_coverage():
    invalid, _ = evaluate(anchor(pair(120), upper_seconds=-1))
    assert invalid.status.value == "invalid_input"
    source = pair()
    sent = next(e for e in source.events if e.type == "sent")
    source = replace(
        source, events=(sent,), e2o=tuple(r for r in source.e2o if r.event == sent.id)
    )
    _, opened = evaluate(source, rule=replace(RULE, observation_policy="open"))
    _, closed = evaluate(source)
    assert opened.status.value == "partial" and opened.value.rules[0].pending_count == 1
    assert (
        closed.status.value == "computed" and closed.value.rules[0].violated_count == 1
    )


def test_f05_no_fabricated_order_for_variants_or_ocdfg():
    log = pair()
    execution = discover_executions(
        log, ExecutionSpec("connected_components", ("task",))
    )
    assert discover_variants(execution, VariantSpec()).status.value == "unavailable"
    assert (
        discover_ocdfg(log, OCDFGSpec(("task",), tie_policy="concurrent")).status.value
        == "invalid_input"
    )
    with pytest.raises(ValueError):
        ExecutionSpec("connected_components", tie_policy="concurrent")


def test_f06_missing_carrier_does_not_join_by_time_and_preserves_unmatched():
    log = pair()
    received = next(e.id for e in log.events if e.type == "received")
    source = replace(
        log,
        e2o=tuple(
            r
            for r in log.e2o
            if not (r.event == received and r.qualifier == "received")
        ),
    )
    result = discover_handover(source, HandoverSpec(actor_object_type="agent"))
    assert not result.value.links and len(result.value.unmatched_sends) == 1
    # A distinct explicit carrier gives unmatched send AND receive; no timestamp join.
    source = replace(
        source,
        objects=source.objects + (Object("message:2", "message"),),
        e2o=source.e2o + (E2O(received, "message:2", "received"),),
    )
    result = discover_handover(source, HandoverSpec(actor_object_type="agent"))
    assert not result.value.links
    assert (
        len(result.value.unmatched_sends) == len(result.value.unmatched_receives) == 1
    )


def test_f06_repeated_carrier_observations_retain_all_e2o_evidence():
    log = pair(30)
    send = next(e for e in log.events if e.type == "sent")
    extra = replace(send, id="repeat")
    log = replace(
        log,
        events=log.events + (extra,),
        e2o=log.e2o
        + tuple(replace(r, event=extra.id) for r in log.e2o if r.event == send.id),
    )
    result = discover_handover(log, HandoverSpec(actor_object_type="agent"))
    assert len(result.value.links) == 2
    for link in result.value.links:
        for relation in link.send_relations + link.receive_relations:
            assert E2O(relation.event, relation.object, relation.qualifier) in log.e2o


def test_f07_changing_group_membership_is_not_collapsed():
    log = pair(30)
    stamp = log.events[0].time
    log = replace(
        log,
        object_types=tuple(
            replace(t, attributes=(Attribute("group", ValueType.STRING),))
            if t.name == "agent"
            else t
            for t in log.object_types
        ),
        objects=tuple(
            replace(
                o,
                attributes=(
                    ObjectAttr("group", "one", stamp),
                    ObjectAttr("group", "two", stamp + timedelta(seconds=1)),
                ),
            )
            if o.type == "agent"
            else o
            for o in log.objects
        ),
    )
    result = discover_handover(
        log, HandoverSpec(actor_object_type="agent", group_by_object_attribute="group")
    )
    assert result.status.value == "invalid_input" and result.value is None


def test_f08_f09_empty_and_dropped_chat_population_keeps_mapping_evidence():
    mapping = ChatLogMapping(
        turn_openers=(MatchRule("start", "kind", "equals", "start"),),
        unmatched_activity="drop_with_count",
    )
    row = {
        "conversation_id": "A",
        "position": 1,
        "author": "A",
        "sent_at": "2026-01-05T09:00Z",
        "kind": "other",
    }
    empty, dropped = import_chat_log([], mapping), import_chat_log([row], mapping)
    assert empty.valid and dropped.valid
    assert not empty.candidate.events and not dropped.candidate.events
    assert empty.mapping_digest == dropped.mapping_digest
    assert dropped.dropped_count == 1 and empty.dropped_count == 0
    # Empty OCEL cannot contain per-event mapping attrs; keep ChatImportResult too.
    changed = import_chat_log([], replace(mapping, text_digest="none"))
    assert changed.mapping_digest != empty.mapping_digest


def test_f08_explicit_id_does_not_fallback_to_sequence_when_missing():
    mapping = ChatLogMapping(
        turn_openers=(MatchRule("sent", "kind", "equals", "sent"),),
        carrier_rules=(
            CarrierRule(
                MatchRule("s", "kind", "equals", "sent"),
                MatchRule("r", "kind", "equals", "received"),
                receiver_field="to",
                explicit_id_field="message_id",
            ),
        ),
    )
    result = import_chat_log(
        [
            {
                "conversation_id": "A",
                "position": 1,
                "author": "A",
                "sent_at": "2026-01-05T09:00Z",
                "kind": "sent",
                "to": "B",
            }
        ],
        mapping,
    )
    assert not result.valid and result.candidate is None and result.import_issues


def test_f09_empty_measurement_is_not_zero_duration_or_proof_of_no_violations():
    log = snapshot()
    log = replace(log, events=(), e2o=())
    temporal = measure_temporal(log, TemporalSpec("task"))
    assert temporal.value.gaps == ()
    traces = reconstruct_traces(log, TraceSpec("task"))
    result = evaluate_constraints(traces, RULE)
    assert result.value.rules[0].activation_count == 0
    assert result.value.rules[0].fulfillment_ratio is None
