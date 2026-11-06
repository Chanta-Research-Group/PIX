"""Executable profile comparison using existing public PIX APIs only.

This synthetic example is not a DFG-to-Petri-net converter, an online object
aligner, or a Pida worker. Copy it and the current_cut fixture outside a checkout
to verify an installed wheel. Output must be a new directory.
"""

import argparse
import hashlib
import json
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path

import pix
from pix.api import (
    ObjectAlignmentSpec,
    ObjectContextSpec,
    align_object_log,
    export_ocel,
    measure_object_context,
    read_ocel,
)
from pix.case_centric.online_alignment import (
    OnlineAlignmentSpec,
    OnlineAlignmentStream,
    build_online_alignment_proxy,
)
from pix.case_centric.sequence_alignment import (
    DFGAlignmentModel,
    DFGAlignmentSpec,
    align_dfg,
)
from pix.case_centric.streaming import StreamEvent, StreamingSpec
from pix.contracts.models import (
    Arc,
    Marking,
    ObjectArc,
    ObjectCentricPetriNet,
    ObjectMarking,
    ObjectToken,
    PetriNet,
    Place,
    Transition,
    TypedPlace,
)
from pix.event_log import CaseAttribute, CaseEvent, CaseLog, CaseTrace, case_traces
from pix.models import read_model, write_model
from pix.ocel import E2O, Event, EventType, Object, ObjectType, build, canonical_digest
from pix.results import read_result, result_json_bytes, write_result

WORD = ("request", "edit", "test", "deliver")
ARTIFACTS = ("artifact-a@r1", "artifact-b@r7")
PROFILE = ObjectAlignmentSpec(("artifact_revision",), qualifiers=("uses",))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def reference_models():
    """Two independently specified models accepting this single word only."""
    graph = DFGAlignmentModel(WORD, tuple(zip(WORD, WORD[1:])), WORD[:1], WORD[-1:])
    net = PetriNet(
        tuple(Place(f"p{i}") for i in range(5)),
        tuple(Transition(f"t{i}", label) for i, label in enumerate(WORD)),
        tuple(
            arc
            for i in range(4)
            for arc in (Arc(f"p{i}", f"t{i}"), Arc(f"t{i}", f"p{i + 1}"))
        ),
        Marking((("p0", 1),)),
        Marking((("p4", 1),)),
    )
    return graph, net


def online_spec(*, generation="synthetic/generation-1", **options):
    return OnlineAlignmentSpec(
        reference_models()[1],
        StreamingSpec(generation, max_cases=4, capacity_policy="reject"),
        proxy_transition_sequences=(("t0", "t1", "t2", "t3"),),
        discount_factor=1,
        decay_time=100,
        **options,
    )


def stream_event(index, activity):
    # Sequence is an explicitly supplied source fact; timestamps are unknown.
    return StreamEvent("case-1", f"observed-{index}", index, activity)


def traces(word):
    return case_traces(
        CaseLog(
            (
                CaseTrace(
                    "case-1",
                    tuple(
                        CaseEvent(
                            f"observed-{i}",
                            (CaseAttribute("concept:name", "string", activity),),
                        )
                        for i, activity in enumerate(word)
                    ),
                ),
            )
        )
    )


def object_model():
    # Both revisions start and verify together; the two reads are independent.
    def marking(place):
        return ObjectMarking(tuple(ObjectToken(place, obj) for obj in ARTIFACTS))

    return ObjectCentricPetriNet(
        tuple(TypedPlace(f"p{i}", "artifact_revision") for i in range(4)),
        (
            Transition("start", "start"),
            Transition("read-a", "read_a"),
            Transition("read-b", "read_b"),
            Transition("verify", "verify"),
        ),
        (
            ObjectArc("p0", "start", True, 2, 2),
            ObjectArc("start", "p1", True, 2, 2),
            ObjectArc("p1", "read-a"),
            ObjectArc("read-a", "p2"),
            ObjectArc("p1", "read-b"),
            ObjectArc("read-b", "p2"),
            ObjectArc("p2", "verify", True, 2, 2),
            ObjectArc("verify", "p3", True, 2, 2),
        ),
        marking("p0"),
        marking("p3"),
        tuple((obj, "artifact_revision") for obj in ARTIFACTS),
    )


def object_log(document):
    events = tuple(
        Event(row["id"], row["activity"], datetime.fromisoformat(row["time"]))
        for row in document["events"]
    )
    built = build(
        object_types=tuple(
            ObjectType(kind)
            for kind in sorted({kind for _, kind in document["objects"]})
        ),
        event_types=tuple(
            EventType(label) for label in sorted({e.type for e in events})
        ),
        objects=tuple(Object(*row) for row in document["objects"]),
        events=events,
        e2o=tuple(
            E2O(row["id"], obj, qualifier)
            for row in document["events"]
            for obj, qualifier in row["relations"]
        ),
    )
    require(built.valid, "Invalid synthetic OCEL input")
    return built.ocel


def calculate(document):
    graph, net = reference_models()
    results = {}
    for name, word in (
        ("prefix", WORD[:2]),
        ("complete", WORD),
        ("review", WORD[:3] + ("review",) + WORD[3:]),
    ):
        results[f"traces_{name}"] = traces(word)
        results[f"batch_{name}"] = align_dfg(results[f"traces_{name}"], graph)
    results["batch_limited"] = align_dfg(
        results["traces_complete"], graph, DFGAlignmentSpec(max_states=1)
    )
    spec = online_spec()
    results["online_proxy"] = build_online_alignment_proxy(spec)
    stream = OnlineAlignmentStream(spec)
    for i, activity in enumerate(WORD[:2]):
        stream.ingest(stream_event(i, activity))
    results["online_open"] = stream.snapshot()
    results["online_checkpoint"] = stream.checkpoint()
    closed_early = OnlineAlignmentStream.resume(results["online_checkpoint"])
    closed_early.close_case("case-1", "explicit-end", 2)
    results["online_closed_early"] = closed_early.snapshot()
    for i, activity in enumerate(WORD[2:], 2):
        stream.ingest(stream_event(i, activity))
    stream.close_case("case-1", "explicit-end", 4)
    results["online_complete"] = stream.snapshot()
    results["proxy_unavailable"] = build_online_alignment_proxy(
        replace(spec, max_proxy_nodes=1)
    )
    log, model = object_log(document), object_model()
    results["objects_complete"] = align_object_log(log, model, PROFILE)
    results["objects_limited"] = align_object_log(
        log, model, replace(PROFILE, max_states=1)
    )
    tied = replace(
        log,
        events=tuple(
            replace(e, time=log.events[1].time) if e.id == "verify" else e
            for e in log.events
        ),
    )
    results["objects_same_object_tie"] = align_object_log(tied, model, PROFILE)
    cut = replace(
        log,
        events=tuple(e for e in log.events if e.id != "verify"),
        e2o=tuple(r for r in log.e2o if r.event != "verify"),
    )
    results["objects_open_as_terminal"] = align_object_log(cut, model, PROFILE)
    results["object_context_cut"] = measure_object_context(
        cut, model, ObjectContextSpec(PROFILE.object_types, PROFILE.qualifiers)
    )
    return (
        results,
        {
            "objects_complete": log,
            "objects_same_object_tie": tied,
            "objects_open_as_terminal": cut,
        },
        {"sequential": net, "objects": model},
    )


def summarize(results):
    rows = {}
    for name, result in results.items():
        if name.startswith("traces_") or name == "online_checkpoint":
            continue
        row = {"status": result.status.value}
        value = result.value
        if name.startswith("batch_"):
            trace = value.traces[0]
            row.update(outcome=trace.status, cost=trace.cost)
        elif name.startswith("online_") and name != "online_proxy":
            case = value.cases[0]
            row.update(
                cost=case.reported_cost,
                closed=case.closed,
                final_cost_unresolved=case.final_cost_unresolved,
                bound_scope=case.bound_scope,
            )
        elif name.startswith("objects_"):
            row.update(
                outcome=None if value is None else value.status,
                cost=None if value is None else value.cost,
            )
            if value is not None and value.move_counts is not None:
                row["moves"] = asdict(value.move_counts)
        elif name == "object_context_cut":
            row.update(
                terminal_prefix_count=value.coverage.terminal_prefix_count,
                final_cut_scored=any(
                    set(c.consumed_event_ids) == {"start", "read-a", "read-b"}
                    for c in value.contexts
                ),
            )
        rows[name] = row
    return rows


def run(fixture, output):
    fixture, output = Path(fixture), Path(output)
    document = json.loads((fixture / "input.json").read_bytes())
    expected = json.loads((fixture / "expected.json").read_bytes())
    results, logs, models = calculate(document)
    actual = summarize(results)
    require(actual == expected, f"Hand-calculated expectations differ: {actual}")
    output.mkdir(parents=True, exist_ok=False)
    for name in ("input.json", "expected.json"):
        (output / name).write_bytes((fixture / name).read_bytes())
    for name, model in models.items():
        path = output / f"{name}.model.json"
        write_model(model, path, origin="provided")
        require(read_model(path).model == model, "Model round-trip differs")
    for name, log in logs.items():
        path = output / f"{name}.ocel.json"
        export_ocel(log, path, format="json")
        require(
            canonical_digest(read_ocel(path)) == canonical_digest(log),
            "OCEL round-trip differs",
        )
    names = {
        result.computation_id: f"{name}.result.json" for name, result in results.items()
    }
    evidence = {}
    for name, result in results.items():
        path = output / f"{name}.result.json"
        write_result(result, path)
        require(read_result(path) == result, "Result round-trip differs")
        evidence[name] = {
            "artifact": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "operator": result.operator_id,
            "operator_version": result.operator_version,
            "status": result.status.value,
            "source_digest": result.source_digest,
            "computation_id": result.computation_id,
            "parent_artifacts": [names[p] for p in result.parent_computation_ids],
            "issues": [issue.code for issue in result.issues],
        }
    restored = OnlineAlignmentStream.resume(
        read_result(output / "online_checkpoint.result.json")
    )
    for i, activity in enumerate(WORD[2:], 2):
        restored.ingest(stream_event(i, activity))
    restored.close_case("case-1", "explicit-end", 4)
    require(
        result_json_bytes(restored.snapshot())
        == result_json_bytes(results["online_complete"]),
        "Resumed future differs",
    )
    record = {
        "example": "pix.current-cut-profile-comparison.v1",
        "pix_version": pix.__version__,
        "summary": actual,
        "results": evidence,
        "input_sha256": hashlib.sha256(
            (fixture / "input.json").read_bytes()
        ).hexdigest(),
        "resume_matches_uninterrupted": True,
        "limits": [
            "Synthetic public-API execution; Pida live integration is not run.",
            "Online costs are approximate upper bounds; status remains partial.",
            "No generic DFG conversion or explicit-DAG/current-cut object alignment.",
            "Unknown times are allowed only with an independently justified source sequence.",
            "No policy, grants, source completeness or deployment acceptance is inferred.",
        ],
    }
    record["artifacts"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.iterdir())
    }
    (output / "run-record.json").write_bytes(json_bytes(record))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = run(args.fixture, args.output)
    print(
        json.dumps(
            {"results": len(record["results"]), "resume_matches_uninterrupted": True}
        )
    )


if __name__ == "__main__":
    main()
