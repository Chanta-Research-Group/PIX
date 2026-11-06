"""Owner acceptance for CR-PIDA-PIX: meanings, limits and native evidence."""

import copy
import hashlib
import json
import runpy
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from pix.api import ObjectAlignmentSpec, align_object_log
from pix.case_centric.online_alignment import OnlineAlignmentSpec, OnlineAlignmentStream
from pix.case_centric.streaming import StreamEvent, StreamingSpec
from pix.ocel import E2O, Event
from pix.results import read_result, result_from_json, result_json_bytes

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/current_cut"
EXAMPLE = runpy.run_path(str(ROOT / "examples/current_cut_demo.py"))
INPUT = json.loads((FIXTURE / "input.json").read_bytes())
WORD = EXAMPLE["WORD"]
PROFILE = EXAMPLE["PROFILE"]


def open_stream(**options):
    stream = OnlineAlignmentStream(EXAMPLE["online_spec"](**options))
    for i, activity in enumerate(WORD[:2]):
        stream.ingest(EXAMPLE["stream_event"](i, activity))
    return stream


def object_input():
    return EXAMPLE["object_log"](INPUT), EXAMPLE["object_model"]()


def test_bundle_has_repeatable_native_results_closed_parents_and_resumable_checkpoint(
    tmp_path,
):
    first = EXAMPLE["run"](FIXTURE, tmp_path / "one")
    second = EXAMPLE["run"](FIXTURE, tmp_path / "two")
    assert first == second
    for name, digest in first["artifacts"].items():
        data = (tmp_path / "one" / name).read_bytes()
        assert data == (tmp_path / "two" / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
    for row in first["results"].values():
        result = read_result(tmp_path / "one" / row["artifact"])
        parents = [
            read_result(tmp_path / "one" / name) for name in row["parent_artifacts"]
        ]
        assert result.parent_computation_ids == tuple(p.computation_id for p in parents)
    assert first["resume_matches_uninterrupted"]


def test_published_reference_artifacts_match_executed_public_calls(tmp_path):
    record = EXAMPLE["run"](FIXTURE, tmp_path / "actual")
    reference = FIXTURE / "reference"
    assert record == json.loads((reference / "run-record.json").read_bytes())
    for name in record["artifacts"]:
        assert (reference / name).read_bytes() == (
            tmp_path / "actual" / name
        ).read_bytes()


def test_wrong_hand_expected_cost_does_not_publish_a_pass(tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "input.json").write_bytes((FIXTURE / "input.json").read_bytes())
    expected = json.loads((FIXTURE / "expected.json").read_bytes())
    expected["batch_prefix"]["cost"] = 0
    (fixture / "expected.json").write_text(json.dumps(expected))
    with pytest.raises(RuntimeError, match="Hand-calculated"):
        EXAMPLE["run"](fixture, tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("length", [1, 2, 3, 4])
def test_each_prefix_omits_only_future_completion_cost_and_close_adds_it(length):
    stream = OnlineAlignmentStream(EXAMPLE["online_spec"]())
    for i, activity in enumerate(WORD[:length]):
        stream.ingest(EXAMPLE["stream_event"](i, activity))
    open_result = stream.snapshot()
    case = open_result.value.cases[0]
    assert case.reported_cost == 0 and case.final_cost_unresolved
    assert case.bound_scope == "model_prefix_alignment_upper_bound"
    assert open_result.status.value == "partial"
    # Independent oracle: this fixed chain has exactly 4-length unobserved acts.
    stream.close_case("case-1", "end", length)
    closed = stream.snapshot().value.cases[0]
    assert closed.reported_cost == 4 - length
    assert closed.closed and not closed.final_cost_unresolved
    assert closed.bound_scope == "accepting_model_alignment_upper_bound"


def test_repeat_delivery_is_idempotent_but_correction_conflict_and_gaps_are_atomic():
    stream = open_stream()
    checkpoint = stream.checkpoint()
    assert stream.ingest(EXAMPLE["stream_event"](1, "edit")).status == "duplicate"
    for event, code in (
        (EXAMPLE["stream_event"](1, "review"), "duplicate_conflict"),
        (EXAMPLE["stream_event"](3, "deliver"), "out_of_order"),
    ):
        with pytest.raises(ValueError, match=code):
            stream.ingest(event)
        assert stream.checkpoint() == checkpoint


def test_new_generation_and_corrected_history_recompute_without_rewriting_old_cut():
    old = open_stream().checkpoint()
    restarted = open_stream(generation="synthetic/generation-2")
    assert restarted.checkpoint().computation_id != old.computation_id
    corrected = OnlineAlignmentStream(
        EXAMPLE["online_spec"](generation="synthetic/correction-1")
    )
    corrected.ingest(EXAMPLE["stream_event"](0, "request"))
    corrected.ingest(EXAMPLE["stream_event"](1, "review"))
    assert corrected.snapshot().value.cases[0].reported_cost == 1
    assert old.value.snapshot.cases[0].reported_cost == 0
    assert OnlineAlignmentStream.resume(old).checkpoint() == old


@pytest.mark.parametrize(
    "field,value", [("operator_version", "999.0.0"), ("source_digest", "changed")]
)
def test_incompatible_checkpoint_is_rejected(field, value):
    checkpoint = open_stream().checkpoint()
    with pytest.raises(ValueError, match="identity mismatch"):
        OnlineAlignmentStream.resume(replace(checkpoint, **{field: value}))


def test_changed_model_spec_does_not_reinterpret_existing_checkpoint():
    checkpoint = open_stream().checkpoint()
    with pytest.raises(ValueError, match="identity mismatch"):
        OnlineAlignmentStream.resume(
            replace(checkpoint, spec=replace(checkpoint.spec, model_move_cost=2))
        )


def test_expansion_and_retention_limits_remain_visible():
    stream = open_stream(max_expansions_per_event=1, witness_history_limit=1)
    result = stream.snapshot()
    assert result.status.value == "partial"
    assert "alignment_witness_history_omitted" in {i.code for i in result.issues}
    assert "online_expansion_limit" in {i.code for i in result.issues}
    restored = OnlineAlignmentStream.resume(
        result_from_json(result_json_bytes(stream.checkpoint()))
    )
    assert restored.snapshot() == result


def test_capacity_rejection_keeps_admitted_coverage():
    spec = EXAMPLE["online_spec"]()
    spec = replace(spec, ingestion=replace(spec.ingestion, max_cases=1))
    stream = OnlineAlignmentStream(spec)
    stream.ingest(EXAMPLE["stream_event"](0, "request"))
    old = stream.checkpoint()
    with pytest.raises(ValueError, match="case_capacity"):
        stream.ingest(StreamEvent("other", "other-0", 0, "request"))
    assert stream.checkpoint() == old
    assert len(stream.snapshot().value.cases) == 1


def test_dfg_is_not_a_petri_net_and_concurrent_is_not_a_supported_order_flag():
    graph, _ = EXAMPLE["reference_models"]()
    with pytest.raises(TypeError, match="PetriNet"):
        OnlineAlignmentSpec(graph, StreamingSpec("test"))
    with pytest.raises(ValueError, match="order_policy"):
        StreamingSpec("test", order_policy="concurrent")
    with pytest.raises(ValueError, match="whole_log"):
        ObjectAlignmentSpec(("artifact_revision",), scope="current_cut")


def test_shared_verification_consumed_once_with_exact_two_revision_bindings():
    log, model = object_input()
    result = align_object_log(log, model, PROFILE)
    assert result.value.cost == 0
    assert result.value.cost_unit == "event_weighted_integer_cost"
    shared = [m for m in result.value.moves if m.event_id == "verify"]
    assert len(shared) == 1 and shared[0].kind == "synchronous"
    assert shared[0].objects == (("artifact_revision", EXAMPLE["ARTIFACTS"]),)
    scope_event = next(e for e in result.value.scope.events if e.event_id == "verify")
    assert scope_event.relations == tuple(
        ("verify", obj, "uses") for obj in EXAMPLE["ARTIFACTS"]
    )
    assert result.value.scope.excluded_object_count == 1
    assert result.value.scope.excluded_relation_count == 4


@pytest.mark.parametrize("rename,skew", [(False, False), (True, False), (True, True)])
def test_independent_reads_do_not_gain_an_edge_from_ids_or_global_time(rename, skew):
    document = copy.deepcopy(INPUT)
    if rename:
        document["events"][1]["id"] = "z-read"
        document["events"][2]["id"] = "a-read"
        document["events"].reverse()
    if skew:
        next(e for e in document["events"] if e["activity"] == "read_a")["time"] = (
            "2026-01-01T00:00:01.500000+00:00"
        )
    log = EXAMPLE["object_log"](document)
    result = align_object_log(log, EXAMPLE["object_model"](), PROFILE)
    assert result.status.value == "computed" and result.value.cost == 0
    reads = {e.id for e in log.events if e.type.startswith("read_")}
    edges = {
        (e.predecessor_event_id, e.successor_event_id)
        for e in result.value.scope.precedence
    }
    assert len(edges) == 4
    assert not any(a in reads and b in reads for a, b in edges)


def test_shared_actor_is_not_an_ordering_scope_and_type_selection_is_not_event_filtering():
    log, model = object_input()
    # The unrelated event remains in whole_log, even without a selected artifact.
    extra = Event("unrelated-task", "start", log.events[0].time + timedelta(seconds=10))
    broad = replace(
        log,
        events=log.events + (extra,),
        e2o=log.e2o + (E2O(extra.id, "agent-shared", "actor"),),
    )
    result = align_object_log(broad, model, PROFILE)
    assert result.value.coverage.input_events == 5
    assert result.value.cost == 1 and result.value.move_counts.log == 1
    assert not any(
        extra.id in (e.predecessor_event_id, e.successor_event_id)
        for e in result.value.scope.precedence
    )
    assert len(result.value.scope.events) == 5


def test_same_artifact_time_tie_stays_unavailable_under_renaming():
    log, model = object_input()
    for name in ("a-verify", "z-verify"):
        tied = replace(
            log,
            events=tuple(
                replace(e, id=name, time=log.events[1].time) if e.id == "verify" else e
                for e in log.events
            ),
            e2o=tuple(
                replace(r, event=name) if r.event == "verify" else r for r in log.e2o
            ),
        )
        result = align_object_log(tied, model, PROFILE)
        assert result.status.value == "unavailable" and result.value is None
        assert {i.code for i in result.issues} == {"ambiguous_event_order"}


def test_changed_artifact_revision_requires_matching_model_universe():
    log, model = object_input()
    old = EXAMPLE["ARTIFACTS"][0]
    new = "artifact-a@r2"
    revised = replace(
        log,
        objects=tuple(replace(o, id=new) if o.id == old else o for o in log.objects),
        e2o=tuple(replace(r, object=new) if r.object == old else r for r in log.e2o),
    )
    result = align_object_log(revised, model, PROFILE)
    assert result.status.value == "invalid_input" and result.value is None
    assert {i.code for i in result.issues} == {
        "object_missing_from_model",
        "model_object_outside_scope",
    }


def test_unknown_time_needs_real_source_sequence_and_cannot_be_an_ocel_point():
    assert open_stream().snapshot().value.cases[0].event_count == 2
    document = copy.deepcopy(INPUT)
    document["events"][0]["time"] = None
    with pytest.raises(TypeError):
        EXAMPLE["object_log"](document)


def test_object_final_alignment_and_context_metric_do_not_claim_current_cut_completion():
    results, _, _ = EXAMPLE["calculate"](INPUT)
    assert results["objects_open_as_terminal"].value.cost == 1
    context = results["object_context_cut"].value
    assert context.coverage.terminal_prefix_count == 1
    assert all(
        set(c.consumed_event_ids) != {"start", "read-a", "read-b"}
        for c in context.contexts
    )


def test_object_binding_limit_preserves_unknown_cost():
    log, model = object_input()
    result = align_object_log(log, model, replace(PROFILE, max_bindings=1))
    assert result.status.value == "partial"
    assert result.value.status == "binding_limit" and result.value.cost is None
    assert result.value.coverage.limited_scopes == 1
