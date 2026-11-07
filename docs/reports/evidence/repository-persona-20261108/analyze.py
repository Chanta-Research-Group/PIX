"""Analyze only the explicitly approved metadata handoff; no producer execution."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
from pix.api import (ExecutionSpec, OCDFGSpec, TraceSpec, VariantSpec,
                     discover_dfg, discover_executions, discover_ocdfg,
                     discover_variants, read_ocel, reconstruct_traces)
from pix.ocel import canonical_digest
from pix.results import read_result, result_json_bytes, write_result

ENGINE = "6e9af5ee1b670de39a87be406518fea49dffdfec"
PRODUCER = "ff68457f7d032bfa0aa81badf27bdf4079cadc5e"
HANDOFF_SHA = "4863f97cf8169f722d901b6ff6d400c59540e80f1c0b5abfac5cb8075667cdac"
PREFIX = "docs/development/repository-catalogue-combination-evidence-20261108/metadata-only"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def attributes(item):
    return {a["name"]: a["value"] for a in item["attributes"]}


def run(checkout, output):
    checkout, output = Path(checkout), Path(output)
    source = checkout / PREFIX
    subprocess.run(["git", "diff", "--exit-code", ENGINE, "--", "src/pix", "pyproject.toml"], cwd=ROOT, check=True)
    handoff_raw = (source / "handoff.json").read_bytes()
    assert sha(handoff_raw) == HANDOFF_SHA
    handoff = json.loads(handoff_raw)
    approved = {"handoff.json": HANDOFF_SHA}
    for record in handoff["records"]:
        approved.update(record["files"])
    raw_files = {}
    for name, expected in approved.items():
        assert Path(name).name == name
        raw = (source / name).read_bytes()
        assert sha(raw) == expected
        assert raw == subprocess.check_output(["git", "-C", str(checkout), "show", f"{PRODUCER}:{PREFIX}/{name}"])
        raw_files[name] = raw
    output.mkdir(parents=True, exist_ok=False)
    saved = output / "approved-source"
    saved.mkdir()
    for name, raw in raw_files.items():
        (saved / name).write_bytes(raw)
    results_by_run = {}
    for record in handoff["records"]:
        ocel_name = next(n for n in record["files"] if n.endswith(".ocel.json"))
        label = ocel_name.removesuffix(".ocel.json")
        document = json.loads(raw_files[ocel_name])
        meta = json.loads(raw_files[label + ".ocel.meta.json"])
        manifest = json.loads(raw_files[label + ".manifest.json"])
        canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        assert sha(canonical) == meta["digest"]
        assert meta["mapping"] == "pida.ocel20/1"
        for key, expected in (("task_id", record["job_id"]), ("run_id", record["run_id"]),
                              ("session_id", record["session_id"]), ("agent_id", record["agent_id"]),
                              ("reported_status", record["status"])):
            assert manifest[key] == expected
        assert manifest["verification_status"] == "UNKNOWN"
        assert "HOST_PROJECT_ARTIFACTS_NOT_CAPTURED" in manifest["known_limits"]
        assert all(manifest[k] == [] for k in ("artifact_refs", "current_artifact_refs", "evidence_refs", "verification_results"))
        assert record["job_id"] != record["organization_task_id"]
        assert record["session_id"] != record["org_id"]
        for typ, key in (("Agent", "agent_id"), ("Task", "task_id"), ("Run", "run_id"), ("Session", "session_id")):
            objects = [o for o in document["objects"] if o["type"] == typ]
            assert len(objects) == 1
            assert attributes(objects[0])[key] == manifest[key]
        event_rows = [{"ocel_id": e["id"], "source_id": attributes(e)["source_id"],
                       "source_event_id": attributes(e)["source_event_id"],
                       "sequence_number": attributes(e)["sequence_number"],
                       "time": e["time"], "activity": e["type"]} for e in document["events"]]
        assert len({(e["source_id"], e["source_event_id"]) for e in event_rows}) == len(event_rows)
        assert len({e["source_id"] for e in event_rows}) == 1
        ordered = sorted(event_rows, key=lambda e: e["sequence_number"])
        assert [e["sequence_number"] for e in ordered] == list(range(1, len(ordered) + 1))
        assert sum(e["activity"] == "context_input_included" for e in ordered) == record["inclusion_events"]
        assert ordered[-1]["activity"] == "run_finished"
        terminal = next(e for e in document["events"] if e["id"] == ordered[-1]["ocel_id"])
        assert attributes(terminal)["payload.status"] == record["status"]
        assert attributes(terminal).get("payload.code") == record["code"]
        log = read_ocel(saved / ocel_name)
        imported = {e.id: e for e in log.events}
        for row in event_rows:
            event = imported[row["ocel_id"]]
            attrs = {a.name: a.value for a in event.attributes}
            assert event.time == datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
            assert attrs["source_event_id"] == row["source_event_id"]
            assert attrs["source_id"] == row["source_id"]
            assert attrs["sequence_number"] == row["sequence_number"]
        kinds = tuple(sorted(t.name for t in log.object_types))
        results = {}
        for kind in kinds:
            spec = TraceSpec(kind, tie_policy="reject")
            results[kind + "_traces"] = reconstruct_traces(log, spec)
            results[kind + "_dfg"] = discover_dfg(log, spec)
        results["ocdfg"] = discover_ocdfg(log, OCDFGSpec(kinds, tie_policy="reject"))
        results["executions"] = discover_executions(log, ExecutionSpec("connected_components", object_types=("Run",), qualifiers=("run",), tie_policy="reject"))
        results["variants"] = discover_variants(results["executions"], VariantSpec())
        names = {result.computation_id: name + ".json" for name, result in results.items()}
        native = output / label
        native.mkdir()
        records = {}
        for name, result in results.items():
            assert all(p in names for p in result.parent_computation_ids)
            path = native / (name + ".json")
            write_result(result, path)
            assert result_json_bytes(read_result(path)) == path.read_bytes()
            records[name] = {"status": result.status.value, "issues": [i.code for i in result.issues],
                             "sha256": sha(path.read_bytes()), "computation_id": result.computation_id,
                             "source_digest": result.source_digest, "parents": [names[p] for p in result.parent_computation_ids]}
        dfg = results["Run_dfg"]
        if dfg.status.value == "computed":
            word = [e["activity"] for e in sorted(event_rows, key=lambda e: e["time"])]
            assert {(e.source_activity, e.target_activity): e.occurrence_count for e in dfg.value.edges} == Counter(zip(word, word[1:]))
        results_by_run[label] = {"handoff_record": record, "source_events": event_rows,
            "counts": {"events": len(log.events), "objects": len(log.objects), "e2o": len(log.e2o), "o2o": len(log.o2o)},
            "timestamp_ties": len(event_rows) - len({e["time"] for e in event_rows}),
            "canonical_ocel": canonical_digest(log).identifier,
            "producer_meta": meta, "manifest": manifest, "native_results": records,
            "coverage": "partial: exact per-run saved metadata; no atomic cross-run cut or host-project artifact capture",
            "snapshot_atomic": False,
            "run_dfg_distinct_edges": len(dfg.value.edges) if dfg.status.value == "computed" else None,
            "run_dfg_occurrences": sum(e.occurrence_count for e in dfg.value.edges) if dfg.status.value == "computed" else None}
    baseline = results_by_run["sdk-profile-a"]["handoff_record"]
    repair = results_by_run["sdk-profile-b"]["handoff_record"]
    assert baseline["status"] == "failed" and baseline["code"] == "PROGRAM_EXIT_FAILED"
    assert repair["status"] == "completed"
    assert all(baseline[k] != repair[k] for k in ("org_id", "job_id", "organization_task_id", "attempt_id", "run_id", "session_id"))
    summary = {"schema": "pix.repository-persona.metadata-compatibility/1", "engine_pin": ENGINE,
        "producer_evidence_commit": PRODUCER, "python": sys.version, "platform": platform.platform(),
        "script_sha256": sha(Path(__file__).read_bytes()), "approved_source_hashes": approved,
        "source_runtime_and_persona_identity": {k:v for k,v in handoff.items() if k not in ("records", "privacy")},
        "identity_scope": "OCEL job/run/session/agent directly checked; OrgTask/attempt/org/Persona selection are approved owner sidecar claims, not reread from private state",
        "source_bundle_digest_scope": "retained owner/exporter digest; raw bundle not accessed or recomputed",
        "unavailable": ["handover: no reviewed message/organization projection", "conformance: no independent reference model", "host project artifact correctness", "cross-run causal order", "organizational efficiency"],
        "runs": results_by_run}
    (output / "run-record.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8", newline="\n")
    print(json.dumps({name: {"counts": row["counts"], "timestamp_ties": row["timestamp_ties"],
        "results": dict(Counter(r["status"] for r in row["native_results"].values())),
        "run_dfg_occurrences": row["run_dfg_occurrences"]} for name,row in results_by_run.items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("approved_checkout")
    parser.add_argument("output")
    args = parser.parse_args()
    run(args.approved_checkout, args.output)
