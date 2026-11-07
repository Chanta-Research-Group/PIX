"""Synthetic two-organization observation fixture using existing PIX operators.

This is a reviewable mapping example, not a production receipt adapter. Source
facts, membership and case sequence must be supplied; none are inferred from
arrival order, timestamps, job IDs, enqueue, or acceptance. Run from this checkout
with src on PYTHONPATH. Output must be a new directory.
"""

import argparse
import hashlib
import json
import runpy
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path

from pix.api import HandoverSpec, TimePrecision, discover_handover, export_ocel
from pix.case_centric.online_alignment import OnlineAlignmentStream
from pix.case_centric.streaming import StreamEvent
from pix.ocel import (
    E2O,
    Attribute,
    Event,
    EventAttr,
    EventType,
    Object,
    ObjectAttr,
    ObjectType,
    ValueType,
    build,
    canonical_digest,
)
from pix.results import read_result, write_result

ROOT = Path(__file__).resolve().parents[1]
CURRENT = runpy.run_path(str(ROOT / "examples/current_cut_demo.py"))
SPEC = HandoverSpec(
    actor_object_type="collaboration_participant",
    sender_qualifiers=("sender",),
    receiver_qualifiers=("receiver",),
    group_by_object_attribute="organization_id",
)
ROLES = {
    "dispatch_observed": ("sent", "sender"),
    "job_enqueued": ("received", "receiver"),
}
KINDS = set(ROLES) | {"context_input_included", "local_acceptance_observed"}
ATTRS = ("source_ref", "source_position", "source_observation_sha256")
LOCAL_SPEC = HandoverSpec(
    actor_object_type="organization",
    sender_qualifiers=("sender",),
    receiver_qualifiers=("recipient",),
    time_precision=TimePrecision(1, attribute="time_granularity_microseconds"),
)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def carrier_id(row, *, owner_scope):
    # A structured tuple avoids delimiter collisions and producer-local ID joins.
    require(
        isinstance(owner_scope, str) and owner_scope,
        "missing_authenticated_owner_scope",
    )
    return "message:" + json.dumps(
        [
            owner_scope,
            row["producer_id"],
            row["request_id"],
            row["recipient_organization_id"],
        ],
        separators=(",", ":"),
    )


def mapped_log(document, cut):
    require(
        document["schema"] == "pix.synthetic-collaboration-observations/1", "schema"
    )
    owner_scope = document.get("authenticated_owner_scope")
    require(
        isinstance(owner_scope, str) and owner_scope,
        "missing_authenticated_owner_scope",
    )
    participants = {row["id"]: row for row in document["participants"]}
    require(len(participants) == len(document["participants"]), "duplicate_participant")
    observations = {row["id"]: row for row in document["observations"]}
    require(len(observations) == len(document["observations"]), "duplicate_observation")
    selected = document["cuts"][cut]
    require(len(set(selected)) == len(selected), "duplicate_cut_event")
    require(set(selected) <= observations.keys(), "unknown_cut_event")
    objects = {}
    events, relations = [], []
    payloads, positions, receipts, delivery_bindings = {}, {}, set(), {}
    for eid in selected:
        row = observations[eid]
        require(row["kind"] in KINDS, "unknown_observation_kind")
        require(row["actor"] in participants, "missing_participant")
        participant = participants[row["actor"]]
        require(
            all(
                isinstance(participant.get(key), str) and participant[key]
                for key in (
                    "organization_id",
                    "host_id",
                    "org_session_id",
                    "agent_id",
                    "binding_revision",
                )
            ),
            "incomplete_participant_binding",
        )
        require(
            isinstance(row.get("source_ref"), str) and row["source_ref"],
            "missing_source_ref",
        )
        source_position = row.get("source_position")
        if source_position is not None:
            require(
                type(source_position) is int and source_position >= 0,
                "invalid_source_position",
            )
            position = (row["source_ref"], source_position)
            require(position not in positions, "source_position_conflict")
            positions[position] = eid
        time = datetime.fromisoformat(row["time"])
        # The fixed fixture binding snapshot is not a temporal membership resolver.
        objects[participant["id"]] = Object(
            participant["id"],
            "collaboration_participant",
            (
                ObjectAttr(
                    "organization_id",
                    participant["organization_id"],
                    datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
                ),
            ),
        )
        attributes = (
            EventAttr("source_ref", row["source_ref"]),
            EventAttr("source_observation_sha256", digest(encoded(row))),
        )
        if source_position is not None:
            attributes += (EventAttr("source_position", source_position),)
        events.append(Event(eid, row["kind"], time, attributes))
        if row["kind"] in ROLES:
            for key in (
                "producer_id",
                "request_id",
                "recipient_organization_id",
                "payload_digest",
            ):
                require(isinstance(row.get(key), str) and row[key], f"missing_{key}")
            carrier = carrier_id(row, owner_scope=owner_scope)
            require(
                carrier not in payloads or payloads[carrier] == row["payload_digest"],
                "carrier_payload_conflict",
            )
            payloads[carrier] = row["payload_digest"]
            if row["kind"] == "job_enqueued":
                require(
                    participant["organization_id"] == row["recipient_organization_id"],
                    "receipt_recipient_mismatch",
                )
                require(
                    isinstance(row.get("job_id"), str) and row["job_id"],
                    "missing_native_job_id",
                )
                require(
                    isinstance(row.get("receipt_id"), str) and row["receipt_id"],
                    "missing_receipt_id",
                )
                binding = (row["job_id"], row["receipt_id"])
                require(
                    carrier not in delivery_bindings
                    or delivery_bindings[carrier] == binding,
                    "carrier_receipt_conflict",
                )
                delivery_bindings[carrier] = binding
                receipt = (row["source_ref"], row["receipt_id"])
                require(receipt not in receipts, "duplicate_receipt")
                receipts.add(receipt)
            objects[carrier] = Object(carrier, "message")
            carrier_role, actor_role = ROLES[row["kind"]]
            relations.extend(
                (E2O(eid, carrier, carrier_role), E2O(eid, row["actor"], actor_role))
            )
        else:
            # Runtime inclusion and acceptance do not become transport receipts.
            relations.append(E2O(eid, row["actor"], "actor"))
    attributes = tuple(
        Attribute(
            name, ValueType.INTEGER if name == "source_position" else ValueType.STRING
        )
        for name in ATTRS
    )
    built = build(
        event_types=tuple(EventType(kind, attributes) for kind in sorted(KINDS)),
        object_types=(
            ObjectType("message"),
            ObjectType(
                "collaboration_participant",
                (Attribute("organization_id", ValueType.STRING),),
            ),
        ),
        events=tuple(events),
        objects=tuple(objects[key] for key in sorted(objects)),
        e2o=tuple(relations),
    )
    require(built.valid, "invalid_mapped_ocel")
    return built.ocel


def sequential_results(source):
    require(
        source["sequence_basis"] == "explicit_per_case_append_sequence",
        "unsupported_sequence_basis",
    )
    require(source["source_ref"].startswith("fixture:"), "synthetic_source_required")
    stream = OnlineAlignmentStream(
        CURRENT["online_spec"](generation=source["source_ref"])
    )
    opened = None
    for index, row in enumerate(source["records"]):
        require(row["timestamp"] is None, "fixture_requires_unknown_time")
        # Preserve the independently supplied case sequence; never enumerate it.
        stream.ingest(
            StreamEvent(
                source["case_id"], row["event_id"], row["sequence"], row["activity"]
            )
        )
        if index == 1:
            opened = stream.snapshot()
    require(opened is not None, "missing_open_cut")
    close = source["close"]
    stream.close_case(source["case_id"], close["event_id"], close["sequence"])
    return {"online_open": opened, "online_complete": stream.snapshot()}


def local_projection(document):
    """Exercise existing local qualifiers; not a copy of Schumpeter's exporter."""
    for name, raw in document["artifact_bytes"].items():
        require(
            document["artifact_revisions"][name] == "sha256:" + digest(raw.encode()),
            "artifact_revision_mismatch",
        )
    log = CURRENT["object_log"](document)
    precision = Attribute("time_granularity_microseconds", ValueType.INTEGER)
    return replace(
        log,
        event_types=tuple(replace(t, attributes=(precision,)) for t in log.event_types),
        events=tuple(
            replace(e, attributes=(EventAttr(precision.name, 1),)) for e in log.events
        ),
    )


def summary(results):
    value = CURRENT["summarize"](
        {k: v for k, v in results.items() if k not in ("early", "late", "local")}
    )
    for name in ("early", "late", "local"):
        result = results[name]
        network = result.value
        require(network is not None, "handover_unavailable")
        value[name] = {
            "status": result.status.value,
            "links": sorted(
                [[x.send_event_id, x.receive_event_id] for x in network.links]
            ),
            "group_edges": [
                [e.sender, e.receiver, e.link_count] for e in network.group_edges
            ],
            "unmatched_sends": list(network.unmatched_sends),
            "unmatched_receives": list(network.unmatched_receives),
            "order_conflicts": [list(pair) for pair in network.order_conflicts],
        }
    return value


def run(fixture, output):
    fixture, output = Path(fixture), Path(output)
    document = json.loads((fixture / "input.json").read_bytes())
    expected = json.loads((fixture / "expected.json").read_bytes())
    logs = {cut: mapped_log(document, cut) for cut in ("early", "late")}
    results = {cut: discover_handover(log, SPEC) for cut, log in logs.items()}
    logs["local"] = local_projection(
        json.loads((fixture / "local_projection.json").read_bytes())
    )
    results["local"] = discover_handover(logs["local"], LOCAL_SPEC)
    results.update(sequential_results(document["sequential_source"]))
    base_fixture = ROOT / "tests/fixtures/current_cut"
    base_results, base_logs, _ = CURRENT["calculate"](
        json.loads((base_fixture / "input.json").read_bytes())
    )
    for name in ("objects_complete", "objects_open_as_terminal"):
        results[name] = base_results[name]
        logs[name] = base_logs[name]
    actual = summary(results)
    require(actual == expected, "hand_expected_mismatch")
    output.mkdir(parents=True, exist_ok=False)
    for name in (
        "input.json",
        "expected.json",
        "local_projection.json",
        "pida-envelope-v1.json",
    ):
        (output / name).write_bytes((fixture / name).read_bytes())
    records = {}
    for name, result in results.items():
        target = output / f"{name}.result.json"
        write_result(result, target)
        require(read_result(target) == result, "native_result_roundtrip")
        records[name] = {
            "artifact": target.name,
            "sha256": digest(target.read_bytes()),
            "source_digest": result.source_digest,
            "computation_id": result.computation_id,
            "operator": result.operator_id,
            "issues": [i.code for i in result.issues],
        }
    for name, log in logs.items():
        export_ocel(log, output / f"{name}.ocel.json", format="json")
    sources = [
        Path(__file__),
        ROOT / "examples/current_cut_demo.py",
        fixture / "input.json",
        fixture / "expected.json",
        fixture / "local_projection.json",
        fixture / "pida-envelope-v1.json",
        base_fixture / "input.json",
        base_fixture / "expected.json",
    ]
    record = {
        "fixture": document["schema"],
        "summary": actual,
        "results": records,
        "ocel_source_digests": {
            k: asdict(canonical_digest(v)) for k, v in logs.items()
        },
        "sources": {
            str(p.resolve().relative_to(ROOT)).replace("\\", "/"): digest(
                p.read_bytes()
            )
            for p in sources
        },
        "artifacts": {p.name: digest(p.read_bytes()) for p in sorted(output.iterdir())},
        "limits": [
            "Synthetic evidence, not a deployed producer adapter or desktop acceptance.",
            "Receipt means durable enqueue, not model input, execution or acceptance.",
            "Case sequence is separate explicit evidence; receipt offsets cannot supply it.",
            "Object terminal completion is not live object-cut conformance.",
            "Participant grouping is a declared immutable binding snapshot.",
        ],
    }
    (output / "run-record.json").write_bytes(encoded(record))
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.fixture, arguments.output)["summary"], indent=2))
