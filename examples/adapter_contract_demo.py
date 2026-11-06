"""Public-API consumer example, not a new PIX importer or Hub manifest contract.

Use --fixture tests/fixtures/pi_hub --output NEW_DIRECTORY. Copy the script and
fixture outside the checkout and run with python -I against an installed wheel.
The fixture declares exact observations; uncertain cases are tested separately.
"""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pix
from pix.api import (
    ConstraintSpec,
    ExecutionSpec,
    HandoverSpec,
    OCDFGSpec,
    PrecedenceRule,
    TemporalSpec,
    TimedResponseRule,
    TraceSpec,
    VariantSpec,
    discover_dfg,
    discover_executions,
    discover_handover,
    discover_ocdfg,
    discover_variants,
    evaluate_constraints,
    export_ocel,
    measure_temporal,
    read_ocel,
    read_result,
    reconstruct_traces,
    result_json_bytes,
    write_result,
)
from pix.ocel import (
    E2O,
    O2O,
    Attribute,
    Event,
    EventAttr,
    EventType,
    Object,
    ObjectType,
    ValueType,
    build,
    canonical_digest,
    validate,
)


def json_bytes(value):
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    ).encode()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def mapping_digest(mapping):
    # This example's explicit encoding; not the chat/table mapping hash format.
    return (
        "example.mapping.v1:sha256:" + hashlib.sha256(json_bytes(mapping)).hexdigest()
    )


def build_snapshot(document, mapping):
    """Map this small synthetic record format through pix.ocel.build only."""
    require(mapping["format"] == "pix.example.normalized-records.v1", "Unknown mapping")
    require(mapping["time_semantics"] == "exact", "This example requires exact times")
    digest = mapping_digest(mapping)
    attributes = tuple(
        Attribute(name, ValueType.STRING)
        for name in ("source_id", "source_event_id", "mapping_digest")
    )
    events, relations = [], []
    for row in document["events"]:
        source_event_id = row[mapping["event_id_field"]]
        event_id = "/".join(
            quote(part, safe="")
            for part in (
                mapping["id_namespace"],
                document["source_id"],
                source_event_id,
            )
        )
        timestamp = row[mapping["time_field"]]
        # Missing/naive times fail; they are never inferred from position or now().
        require(isinstance(timestamp, str), "An observed timestamp is required")
        events.append(
            Event(
                event_id,
                row[mapping["activity_field"]],
                datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                (
                    EventAttr("source_id", document["source_id"]),
                    EventAttr("source_event_id", source_event_id),
                    EventAttr("mapping_digest", digest),
                ),
            )
        )
        relations.extend(E2O(event_id, obj, role) for obj, role in row["relationships"])
    return build(
        event_types=tuple(
            EventType(t, attributes) for t in sorted({e.type for e in events})
        ),
        object_types=tuple(
            ObjectType(t) for t in sorted({o["type"] for o in document["objects"]})
        ),
        events=events,
        objects=tuple(Object(row["id"], row["type"]) for row in document["objects"]),
        e2o=relations,
        o2o=tuple(O2O(**row) for row in document["object_relations"]),
    )


def analyze(log):
    """No implicit conversion from traces to object-centric executions."""
    traces = reconstruct_traces(log, TraceSpec("task", qualifiers=("task",)))
    executions = discover_executions(
        log, ExecutionSpec("connected_components", object_types=("task",))
    )
    return {
        "traces": traces,
        "executions": executions,
        "variants": discover_variants(executions, VariantSpec()),
        "task_dfg": discover_dfg(log, TraceSpec("task", qualifiers=("task",))),
        "ocdfg": discover_ocdfg(log, OCDFGSpec(("task",), qualifiers=("task",))),
        "constraints": evaluate_constraints(
            traces,
            ConstraintSpec(
                (
                    PrecedenceRule(
                        "artifact_before_check",
                        "artifact_written",
                        "verification_executed",
                    ),
                    TimedResponseRule(
                        "ack_60s", "sent", "received", 0, 60_000_000, "first"
                    ),
                ),
                "closed",
            ),
        ),
        "temporal": measure_temporal(log, TemporalSpec("task", qualifiers=("task",))),
        "handover": discover_handover(log, HandoverSpec(actor_object_type="agent")),
    }


def summary(log, results):
    require(
        all(r.status.value == "computed" for r in results.values()),
        "Unexpected result status",
    )
    handover = results["handover"].value
    return {
        "event_count": len(log.events),
        "object_count": len(log.objects),
        "e2o_count": len(log.e2o),
        "o2o_count": len(log.o2o),
        "task_sequence": [e.activity for e in results["traces"].value.traces[0].events],
        "execution_count": len(results["executions"].value.executions),
        "variant_frequencies": [
            v.frequency for v in results["variants"].value.variants
        ],
        "task_dfg_edges": sorted(
            [e.source_activity, e.target_activity, e.occurrence_count]
            for e in results["ocdfg"].value.graphs[0].edges
        ),
        "constraint_counts": {
            r.rule_id: [
                r.fulfilled_count,
                r.violated_count,
                r.pending_count,
                r.indeterminate_count,
            ]
            for r in results["constraints"].value.rules
        },
        "task_gap_microseconds": sorted(
            s.duration_microseconds
            for edge in results["temporal"].value.gaps
            for s in edge.duration.samples
        ),
        "handover": [
            [
                link.sender,
                link.receiver,
                link.carrier_object_id,
                link.latency_lower_microseconds,
                link.latency_upper_microseconds,
            ]
            for link in handover.links
        ],
        "unmatched_sends": list(handover.unmatched_sends),
        "unmatched_receives": list(handover.unmatched_receives),
        "order_conflicts": [list(pair) for pair in handover.order_conflicts],
    }


def run(fixture, output, *, pix_commit=None, wheel=None):
    if pix_commit is not None:
        require(
            re.fullmatch(r"[0-9a-f]{40}", pix_commit) is not None,
            "Use a full commit SHA",
        )
    inputs = {
        name: (fixture / name).read_bytes()
        for name in ("normalized.json", "mapping.json", "expected.json")
    }
    document, mapping = (
        json.loads(inputs["normalized.json"]),
        json.loads(inputs["mapping.json"]),
    )
    built = build_snapshot(document, mapping)
    require(built.valid, f"Invalid snapshot: {built.report}")
    log = built.ocel
    require(validate(log).valid, "Snapshot validation failed")
    results = analyze(log)
    observed = summary(log, results)
    require(
        observed == json.loads(inputs["expected.json"]),
        "Hand-calculated fixture expectations differ",
    )
    repeated = analyze(log)
    require(
        all(
            result_json_bytes(r) == result_json_bytes(repeated[n])
            for n, r in results.items()
        ),
        "Nondeterministic native result",
    )
    output.mkdir(parents=True, exist_ok=False)
    for name, content in inputs.items():
        (output / name).write_bytes(content)
    exports = {}
    for fmt in ("json", "xml", "sqlite"):
        path = output / f"snapshot.{fmt}"
        exported = export_ocel(log, path, format=fmt)
        restored = read_ocel(path)
        require(
            canonical_digest(restored) == canonical_digest(log),
            "OCEL round-trip changed facts",
        )
        roundtrip_results = analyze(restored)
        require(
            all(
                result_json_bytes(r) == result_json_bytes(roundtrip_results[n])
                for n, r in results.items()
            ),
            "Round-trip changed analysis",
        )
        exports[fmt] = {
            "artifact": path.name,
            "sha256": exported.output_sha256,
            "roundtrip": exported.roundtrip,
            "reference_schema": exported.reference_schema,
        }
    artifact_index = {
        r.computation_id: f"{name}.result.json" for name, r in results.items()
    }
    records = {}
    for name, result in results.items():
        require(
            all(parent in artifact_index for parent in result.parent_computation_ids),
            "Missing parent artifact",
        )
        path = output / artifact_index[result.computation_id]
        write_result(result, path)
        require(read_result(path) == result, "Result round-trip changed evidence")
        records[name] = {
            "artifact": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "computation_id": result.computation_id,
            "status": result.status.value,
            "parent_artifacts": [
                artifact_index[parent] for parent in result.parent_computation_ids
            ],
        }
    evidence = {
        "scope": "Synthetic consumer example, not Schumpeter G1 or mission acceptance",
        "pix_version": pix.__version__,
        "pix_commit_declared": pix_commit,
        "wheel_sha256_declared": hashlib.sha256(wheel.read_bytes()).hexdigest()
        if wheel
        else None,
        "installed_pix": str(Path(pix.__file__).resolve()),
        "installed_distributions": sorted(
            f"{dist.metadata['Name']}=={dist.version}"
            for dist in importlib.metadata.distributions()
        ),
        "python": sys.version,
        "platform": platform.platform(),
        "isolated": bool(sys.flags.isolated),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": {
            name: hashlib.sha256(data).hexdigest() for name, data in inputs.items()
        },
        "source_digest": canonical_digest(log).identifier,
        "mapping_digest": mapping_digest(mapping),
        "coverage": {
            "source_events": len(document["events"]),
            "projected_events": len(log.events),
            "excluded_events": 0,
            "scope": "provided synthetic file only",
        },
        "summary": observed,
        "exports": exports,
        "results": records,
        "limits": [
            "Exact-time example only",
            "Verification execution is not verification success",
            "Service time unavailable without observed start attributes",
        ],
    }
    (output / "run-record.json").write_bytes(json_bytes(evidence))
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--pix-commit", help="Caller-declared build SHA; not inferred or authenticated"
    )
    parser.add_argument(
        "--wheel", type=Path, help="Caller-declared installed wheel for byte identity"
    )
    args = parser.parse_args()
    record = run(
        args.fixture, args.output, pix_commit=args.pix_commit, wheel=args.wheel
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "source_digest": record["source_digest"],
                "output": str(args.output),
            }
        )
    )
