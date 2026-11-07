"""Analyze copied historical Pida evidence only, with unmodified PIX public APIs."""

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from pix.api import (  # noqa: E402
    ExecutionSpec, HandoverSpec, OCDFGSpec, TemporalSpec, TimePrecision, TraceSpec,
    VariantSpec, discover_dfg, discover_executions, discover_handover, discover_ocdfg,
    discover_variants, import_ocel, measure_temporal, reconstruct_traces,
)
from pix.ocel import canonical_digest  # noqa: E402
from pix.results import read_result, result_json_bytes, write_result  # noqa: E402

ENGINE_PIN = "3205d832d5dcdc6901f916b35496a0c60b657e7a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(output):
    # This is source equivalence, not acceptance by a consumer commit allowlist.
    subprocess.run(["git", "diff", "--exit-code", ENGINE_PIN, "HEAD", "--", "src/pix", "pyproject.toml"], cwd=ROOT, check=True)
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", "src/pix", "pyproject.toml"], cwd=ROOT, check=True)
    bundle = json.loads((HERE / "source/observation-bundle.json").read_bytes())
    exported = json.loads((HERE / "export.json").read_bytes())
    loaded = import_ocel(HERE / "actual.ocel.json")
    assert loaded.ocel is not None, loaded
    log = loaded.ocel
    events = bundle["events"]
    assert len({(e["source_id"], e["session_id"], e["run_id"]) for e in events}) == 1
    assert [e["sequence_number"] for e in events] == list(range(1, len(events) + 1))
    assert [e["occurred_at"] for e in events] == sorted(e["occurred_at"] for e in events)
    assert len(set(e["occurred_at"] for e in events)) == len(events)
    assert len(log.events) == len(events) == 9
    native_source_ids = {
        next(a.value for a in e.attributes if a.name == "source_event_id") for e in log.events
    }
    assert native_source_ids == {e["source_event_id"] for e in events}
    for source in events:
        mapped = next(e for e in log.events if any(a.name == "source_event_id" and a.value == source["source_event_id"] for a in e.attributes))
        assert mapped.time.isoformat(timespec="milliseconds").replace("+00:00", "Z") == source["occurred_at"]
        assert next(a.value for a in mapped.attributes if a.name == "sequence_number") == source["sequence_number"]
    kinds = tuple(sorted(t.name for t in log.object_types))
    results = {}
    for kind in kinds:
        spec = TraceSpec(kind, tie_policy="reject")
        results[f"traces_{kind}"] = reconstruct_traces(log, spec)
        results[f"dfg_{kind}"] = discover_dfg(log, spec)
    results["ocdfg"] = discover_ocdfg(log, OCDFGSpec(kinds, tie_policy="reject"))
    results["executions"] = discover_executions(log, ExecutionSpec(
        "connected_components", object_types=("Run",), qualifiers=("run",), tie_policy="reject"))
    results["variants"] = discover_variants(results["executions"], VariantSpec())
    results["traces_Run_millisecond"] = reconstruct_traces(log, TraceSpec("Run", qualifiers=("run",), time_precision=TimePrecision(1000)))
    results["temporal_Run"] = measure_temporal(log, TemporalSpec("Run", qualifiers=("run",), time_precision=TimePrecision(1000)))
    results["handover_not_applicable"] = discover_handover(log, HandoverSpec(actor_object_type="Agent", carrier_object_type="Message"))
    expected_edges = {"Agent": 8, "Session": 8, "Task": 8, "Run": 8, "Turn": 4, "ModelRequest": 2}
    for kind, count in expected_edges.items():
        result = results[f"dfg_{kind}"]
        assert result.status.value == "computed" and len(result.value.edges) == count
        assert all(edge.occurrence_count == 1 for edge in result.value.edges)
    assert results["handover_not_applicable"].status.value == "invalid_input"
    names = {result.computation_id: f"{name}.result.json" for name, result in results.items()}
    assert all(parent in names for result in results.values() for parent in result.parent_computation_ids)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = {}
    for name, result in results.items():
        path = output / f"{name}.result.json"
        write_result(result, path)
        assert result_json_bytes(read_result(path)) == path.read_bytes()
        records[name] = {
            "status": result.status.value, "issues": [i.code for i in result.issues],
            "operator": result.operator_id, "source_digest": result.source_digest,
            "computation_id": result.computation_id, "artifact": path.name,
            "parent_artifacts": [names[parent] for parent in result.parent_computation_ids],
            "sha256": sha(path.read_bytes()),
        }
    descriptor = json.loads(next(e["payload"]["descriptor"] for e in events if e["activity"] == "context_snapshot_loaded"))
    external = descriptor["personaBinding"]["externalContext"]
    record = {
        "kind": "historical-single-live-model-smoke-public-api-investigation",
        "engine_source_equivalent_to_pin": ENGINE_PIN,
        "imported_checkout_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "source_files": {
            p.relative_to(HERE).as_posix(): sha(p.read_bytes()) for p in [
                HERE / "source/observation-bundle.json", HERE / "source/result.json", HERE / "source/start.json",
                HERE / "export.json", HERE / "actual.ocel.json", HERE / "export-record.json", Path(__file__),
            ]},
        "canonical_ocel_digest": asdict(canonical_digest(log)),
        "import": {"status": loaded.status.value, "source_sha256": loaded.source_sha256,
                   "issues": [i.code for i in loaded.import_issues],
                   "transformations": [asdict(t) for t in loaded.transformations]},
        "counts": {"events": len(log.events), "objects": len(log.objects), "e2o": len(log.e2o), "o2o": len(log.o2o),
                   "activities": dict(Counter(e.type for e in log.events)), "object_types": dict(Counter(o.type for o in log.objects))},
        "sequence_scope": {"source_id": events[0]["source_id"], "session_id": bundle["session_id"], "run_id": bundle["run_id"],
                           "observed_range": [1,9], "contiguous": True, "timestamp_ties": [], "times_unmodified": True,
                           "meaning": "Per-run journal observation order, not cross-agent/network causality"},
        "coverage": {"bundle_complete": bundle["complete"], "bundle_limits": bundle["known_limits"],
                     "export_limits": exported["knownLimits"], "manifest_limits": bundle["manifest"]["known_limits"],
                     "verification_status": bundle["manifest"]["verification_status"]},
        "historical_external_binding": {k: external[k] for k in ("hostId", "organizationSessionId", "agentInstanceId", "taskId", "attemptId", "runId", "bindingId")},
        "results": records,
        "dfg_counts": {kind: {"objects": results[f"dfg_{kind}"].value.object_count,
                                "edges": len(results[f"dfg_{kind}"].value.edges),
                                "occurrences": sum(e.occurrence_count for e in results[f"dfg_{kind}"].value.edges)} for kind in kinds},
        "temporal": asdict(results["temporal_Run"].value),
        "unrun_questions": {"alignment": "No independent DFG/Petri-net/OCPN reference model supplied; no conformance cost computed",
                            "online": "No adopted model or stream identity supplied; not started from an invented model",
                            "cross_org": "No organization/message carrier or remote receipt object in this single run",
                            "artifact_correctness": "No artifact/verification objects; manifest task verification UNKNOWN",
                            "improvement": "Unknown; one task is not comparative efficiency evidence"},
    }
    (output / "run-record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"counts": record["counts"], "dfg": record["dfg_counts"], "results": {k:v["status"] for k,v in records.items()}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
