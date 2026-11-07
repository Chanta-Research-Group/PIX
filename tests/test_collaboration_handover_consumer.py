"""Independent mapping-oracle checks, not desktop or producer acceptance."""

import copy
import hashlib
import json
import runpy
from dataclasses import replace
from pathlib import Path

import pytest

from pix.api import discover_handover
from pix.results import read_result, result_json_bytes

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/collaboration_handover"
EXAMPLE = runpy.run_path(str(ROOT / "examples/collaboration_handover_demo.py"))
INPUT = json.loads((FIXTURE / "input.json").read_bytes())


def observation(document, eid):
    return next(row for row in document["observations"] if row["id"] == eid)


def calculate(document=INPUT, cut="late"):
    return discover_handover(EXAMPLE["mapped_log"](document, cut), EXAMPLE["SPEC"])


def test_hand_oracle_and_native_artifacts_are_repeatable(tmp_path):
    first = EXAMPLE["run"](FIXTURE, tmp_path / "first")
    second = EXAMPLE["run"](FIXTURE, tmp_path / "second")
    assert first == second
    for name, expected in first["artifacts"].items():
        raw = (tmp_path / "first" / name).read_bytes()
        assert raw == (tmp_path / "second" / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected
    for row in first["results"].values():
        raw = (tmp_path / "first" / row["artifact"]).read_bytes()
        assert (
            result_json_bytes(read_result(tmp_path / "first" / row["artifact"])) == raw
        )


def test_wrong_hand_oracle_cannot_publish_pass(tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "input.json").write_bytes((FIXTURE / "input.json").read_bytes())
    (fixture / "local_projection.json").write_bytes(
        (FIXTURE / "local_projection.json").read_bytes()
    )
    expected = json.loads((FIXTURE / "expected.json").read_bytes())
    expected["late"]["unmatched_receives"] = []
    (fixture / "expected.json").write_text(json.dumps(expected))
    with pytest.raises(ValueError, match="hand_expected_mismatch"):
        EXAMPLE["run"](fixture, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_late_evidence_closes_only_exact_carrier_and_keeps_clock_conflict():
    early, late = calculate(cut="early"), calculate()
    assert early.value.unmatched_sends == ("send-pending", "send-request")
    assert late.value.unmatched_sends == ("send-pending",)
    assert late.value.unmatched_receives == ("receive-orphan",)
    assert late.value.order_conflicts == (("send-request", "receive-request"),)
    request = next(
        link for link in late.value.links if link.send_event_id == "send-request"
    )
    assert request.latency_upper_microseconds == -1_000_000
    assert {(e.sender, e.receiver, e.link_count) for e in late.value.group_edges} == {
        ("org-a", "org-b", 1),
        ("org-b", "org-a", 1),
    }
    assert "handover_order_conflicts" in {i.code for i in late.issues}


def test_arrival_order_and_unrelated_interleaving_do_not_change_native_result():
    document = copy.deepcopy(INPUT)
    document["observations"].reverse()
    document["cuts"]["late"].reverse()
    assert result_json_bytes(calculate(document)) == result_json_bytes(calculate())
    value = calculate().value
    referenced = {
        eid for x in value.links for eid in (x.send_event_id, x.receive_event_id)
    }
    assert not {"unrelated-input", "accept-local"} & referenced


def test_receipt_only_is_not_fabricated_send_or_response():
    document = copy.deepcopy(INPUT)
    document["cuts"]["late"] = ["receive-request"]
    result = calculate(document)
    assert result.value.links == ()
    assert result.value.unmatched_receives == ("receive-request",)
    assert (
        result.status.value == "computed"
    )  # Computable network, not complete delivery.


def test_same_carrier_cannot_silently_change_native_job_binding():
    document = copy.deepcopy(INPUT)
    duplicate = copy.deepcopy(observation(document, "receive-request"))
    duplicate.update(
        id="receive-request-conflict",
        receipt_id="another-receipt",
        job_id="another-native-job",
        source_position=2,
    )
    document["observations"].append(duplicate)
    document["cuts"]["late"].append(duplicate["id"])
    with pytest.raises(ValueError, match="carrier_receipt_conflict"):
        calculate(document)


def test_matching_job_or_payload_cannot_join_different_request_or_recipient():
    for field, new_value in (
        ("request_id", "another-request"),
        ("recipient_organization_id", "other-org"),
    ):
        document = copy.deepcopy(INPUT)
        observation(document, "send-request")[field] = new_value
        result = calculate(document)
        assert "receive-request" in result.value.unmatched_receives
        assert "send-request" in result.value.unmatched_sends


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("payload", "carrier_payload_conflict"),
        ("recipient", "receipt_recipient_mismatch"),
        ("position", "source_position_conflict"),
        ("bad_position", "invalid_source_position"),
        ("missing_job", "missing_native_job_id"),
        ("duplicate_cut", "duplicate_cut_event"),
        ("duplicate_event", "duplicate_observation"),
        ("binding", "incomplete_participant_binding"),
    ],
)
def test_invalid_mapping_does_not_repair_source(mutation, reason):
    document = copy.deepcopy(INPUT)
    receive = observation(document, "receive-request")
    if mutation == "payload":
        receive["payload_digest"] = "sha256:" + "9" * 64
    elif mutation == "recipient":
        receive["actor"] = "participant-a@binding-1"
    elif mutation == "position":
        receive["source_position"] = 1
    elif mutation == "bad_position":
        receive["source_position"] = True
    elif mutation == "missing_job":
        del receive["job_id"]
    elif mutation == "duplicate_cut":
        document["cuts"]["late"].append("receive-request")
    elif mutation == "duplicate_event":
        document["observations"].append(copy.deepcopy(receive))
    else:
        del document["participants"][0]["binding_revision"]
    with pytest.raises(ValueError, match=reason):
        calculate(document)


def test_receipt_offsets_cannot_be_substituted_for_case_sequence():
    source = copy.deepcopy(INPUT["sequential_source"])
    source["sequence_basis"] = "receipt_arrival_order"
    with pytest.raises(ValueError, match="unsupported_sequence_basis"):
        EXAMPLE["sequential_results"](source)
    source["sequence_basis"] = "explicit_per_case_append_sequence"
    source["records"][1]["sequence"] = 2
    with pytest.raises(ValueError, match="out_of_order"):
        EXAMPLE["sequential_results"](source)


def test_open_case_is_partial_and_terminal_object_cost_is_not_live_failure(tmp_path):
    EXAMPLE["run"](FIXTURE, tmp_path / "out")
    opened = read_result(tmp_path / "out/online_open.result.json")
    assert opened.status.value == "partial"
    assert opened.value.cases[0].reported_cost == 0
    assert opened.value.cases[0].final_cost_unresolved
    terminal = read_result(tmp_path / "out/objects_open_as_terminal.result.json")
    assert terminal.value.cost == 1 and terminal.value.status == "optimal"
    complete = read_result(tmp_path / "out/objects_complete.result.json")
    verify = [m for m in complete.value.moves if m.event_id == "verify"]
    assert len(verify) == 1
    assert verify[0].objects == (
        ("artifact_revision", ("artifact-a@r1", "artifact-b@r7")),
    )
    assert not any(
        e.predecessor_event_id in {"read-a", "read-b"}
        and e.successor_event_id in {"read-a", "read-b"}
        for e in complete.value.scope.precedence
    )


def test_dynamic_membership_is_not_collapsed_to_latest_group():
    log = EXAMPLE["mapped_log"](INPUT, "late")
    participant = next(o for o in log.objects if o.id == "participant-a@binding-1")
    changed = replace(
        participant.attributes[0],
        value="org-b",
        time=participant.attributes[0].time.replace(second=30),
    )
    log = replace(
        log,
        objects=tuple(
            replace(o, attributes=o.attributes + (changed,))
            if o.id == participant.id
            else o
            for o in log.objects
        ),
    )
    result = discover_handover(log, EXAMPLE["SPEC"])
    assert result.status.value == "invalid_input"
    assert "missing_or_dynamic_handover_group" in {i.code for i in result.issues}


def test_existing_local_source_qualifiers_keep_receipt_and_artifact_review_separate():
    document = json.loads((FIXTURE / "local_projection.json").read_bytes())
    log = EXAMPLE["local_projection"](document)
    result = discover_handover(log, EXAMPLE["LOCAL_SPEC"])
    assert [
        (link.send_event_id, link.receive_event_id) for link in result.value.links
    ] == [("local-post", "local-receipt")]
    # A recipient on the post, and responds_to on the answer, are not receipts.
    assert result.value.unmatched_sends == ("local-answer",)
    review = [e for e in log.events if e.type == "contract.review"]
    assert len(review) == 1
    relations = {(r.object, r.qualifier) for r in log.e2o if r.event == review[0].id}
    revisions = set(document["artifact_revisions"].values())
    assert {
        obj for obj, qualifier in relations if qualifier == "evaluated"
    } == revisions
    assert (
        "sha256:" + hashlib.sha256(document["criterion_bytes"].encode()).hexdigest(),
        "evaluated_against",
    ) in relations
    assert (
        hashlib.sha256(document["acceptance_bytes"].encode()).hexdigest(),
        "records",
    ) in relations
    document["artifact_bytes"]["result-a.json"] = '{"total":43}\n'
    with pytest.raises(ValueError, match="artifact_revision_mismatch"):
        EXAMPLE["local_projection"](document)


def test_actual_envelope_identity_is_distinct_from_native_execution_job():
    raw = (FIXTURE / "pida-envelope-v1.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "ee7386c009799ac52b976b26c99b45b4fceae4dc78338581045da8c71aebfdfe"
    )
    envelope = json.loads(raw)
    body = {k: v for k, v in envelope.items() if k != "payload_digest"}
    canonical = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == envelope["payload_digest"]
    assert "job_id" not in envelope and "source_position" not in envelope
    identity = {
        "producer_id": envelope["producer_id"],
        "request_id": envelope["request_id"],
        "recipient_organization_id": envelope["recipient"]["organization_id"],
    }
    assert (
        EXAMPLE["carrier_id"](identity, owner_scope="authenticated-owner-a")
        == 'message:["authenticated-owner-a","schumpeter","message-001","org-A"]'
    )
    # No offset is manufactured for handover; the case stream still needs separate evidence.
    document = copy.deepcopy(INPUT)
    for row in document["observations"]:
        row.pop("source_position")
    log = EXAMPLE["mapped_log"](document, "late")
    assert not any(
        a.name == "source_position" for e in log.events for a in e.attributes
    )
    assert len(discover_handover(log, EXAMPLE["SPEC"]).value.links) == 2


def test_authenticated_owner_scope_is_required_and_carriers_never_alias():
    first = EXAMPLE["mapped_log"](INPUT, "late")
    other = copy.deepcopy(INPUT)
    other["authenticated_owner_scope"] = "fixture-owner-b"
    second = EXAMPLE["mapped_log"](other, "late")
    assert {o.id for o in first.objects if o.type == "message"}.isdisjoint(
        {o.id for o in second.objects if o.type == "message"}
    )
    del other["authenticated_owner_scope"]
    with pytest.raises(ValueError, match="missing_authenticated_owner_scope"):
        EXAMPLE["mapped_log"](other, "late")
