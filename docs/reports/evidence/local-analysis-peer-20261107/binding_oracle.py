"""Owner peer fixture: frozen mock admission metadata, no runtime or private input."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
from pix.api import (ExecutionSpec, TraceSpec, VariantSpec, discover_dfg,
                     discover_executions, discover_variants, read_ocel,
                     reconstruct_traces)
from pix.results import read_result, result_json_bytes, write_result

FROZEN = "81c8a9485b2ca0df9bb9c971e45b90107aa25e94"
SOURCE = "docs/development/evidence/pida-admission-20261107"


def run(checkout, output):
    checkout, output = Path(checkout), Path(output)
    blobs = {name: subprocess.check_output(["git", "-C", str(checkout), "show", f"{FROZEN}:{SOURCE}/{name}"])
             for name in ("actual-admission.json", "first-root.bundle.json", "first-root.ocel.json")}
    data, bundle, exported = [json.loads(blobs[name]) for name in blobs]
    receipt, job = data["first_receipt"], data["first_job"]
    assert data["real_model_calls"] is False and data["multiple_agents_executed"] is False
    assert receipt["job_id"] == job["id"] == bundle["manifest"]["task_id"]
    assert receipt["root_task_id"] == job["organizationTaskId"] != job["id"]
    assert receipt["root_attempt_id"] == job["attemptId"]
    assert receipt["recipient"]["agent_id"] == job["agentId"]
    assert job["runId"] == bundle["run_id"]
    assert job["sessionId"] == bundle["session_id"] != receipt["recipient"]["org_session_id"]
    source_events = [e for e in data["source_events"]["events"] if e["payload"]["reservation_id"] == receipt["reservation_id"]]
    observed = next(e for e in source_events if e["kind"] == "organization_admission_observed")
    binding = observed["payload"]["recipient_binding"]
    assert observed["payload"]["reservation_state"] == "observed"
    assert observed["payload"]["runtime_existence"] == "native_readback"
    for source_key, target_key in (("org_id", "organization_id"), ("host_id", "host_id"), ("org_session_id", "org_session_id"), ("agent_id", "agent_id")):
        assert binding[source_key] == receipt["recipient"][target_key]
    for e in source_events:
        for name in ("payload_digest", "definition_digest", "admission_digest", "reservation_id", "producer_id", "request_id"):
            assert e["payload"][name] == receipt[name]
    assert data["operator_binding"]["kind"] == "operator"
    assert not {"agent_id", "host_id", "org_session_id"} & data["operator_binding"].keys()
    assert {e["agent_id"] for e in bundle["events"]} == {job["agentId"]}
    assert [e["sequence_number"] for e in bundle["events"]] == list(range(1, 17))
    assert len({e["occurred_at"] for e in bundle["events"]}) == 16
    output.mkdir(parents=True, exist_ok=False)
    (output / "actual-metadata.ocel.json").write_text(json.dumps(exported["document"], indent=2) + "\n", encoding="utf-8", newline="\n")
    log = read_ocel(output / "actual-metadata.ocel.json")
    trace = reconstruct_traces(log, TraceSpec("Run", qualifiers=("run",), tie_policy="reject"))
    dfg = discover_dfg(log, TraceSpec("Run", qualifiers=("run",), tie_policy="reject"))
    executions = discover_executions(log, ExecutionSpec("connected_components", object_types=("Run",), qualifiers=("run",), tie_policy="reject"))
    variants = discover_variants(executions, VariantSpec())
    word = [e["activity"] for e in bundle["events"]]
    expected_edges = Counter(zip(word, word[1:]))
    assert {(e.source_activity, e.target_activity): e.occurrence_count for e in dfg.value.edges} == expected_edges
    results = {"run_traces": trace, "run_dfg": dfg, "run_executions": executions, "run_variants": variants}
    names = {r.computation_id: name + ".json" for name, r in results.items()}
    records = {}
    for name, result in results.items():
        path = output / (name + ".json")
        write_result(result, path)
        assert result_json_bytes(read_result(path)) == path.read_bytes()
        records[name] = {"status": result.status.value, "artifact": path.name,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "computation_id": result.computation_id, "source_digest": result.source_digest,
                         "parents": [names[p] for p in result.parent_computation_ids],
                         "issues": [i.code for i in result.issues]}
    oracle = {
        "fixture": "pix.owner-peer-local-pida-binding/1", "scope": "frozen actual scripted mock runtime evidence, not a new model call or production source approval",
        "producer_evidence_commit": FROZEN,
        "source_hashes": {name: hashlib.sha256(raw).hexdigest() for name, raw in blobs.items()},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "owner_scope": observed["payload"]["owner_scope"],
        "carrier": {"producer_id": receipt["producer_id"], "request_id": receipt["request_id"], "recipient_organization_id": receipt["recipient"]["organization_id"]},
        "receipt": receipt, "operator_binding": data["operator_binding"], "observed_recipient_binding": binding,
        "native_job": {k: job[k] for k in ("id", "agentId", "organizationTaskId", "attemptId", "sessionId", "runId", "status")},
        "source_event_refs": [{"id": e["id"], "sequence": e["sequence"], "kind": e["kind"], "occurred_at": e["occurred_at"]} for e in source_events],
        "binding_evidence_event": observed["id"], "handover": "UNAVAILABLE: admission intent/attempt/receipt are not a reviewed logical-message handover projection",
        "counts": {"events": len(log.events), "objects": len(log.objects), "e2o": len(log.e2o), "o2o": len(log.o2o), "run_dfg_distinct_edges": len(dfg.value.edges), "run_dfg_occurrences": sum(e.occurrence_count for e in dfg.value.edges)},
        "coverage": {"bundle_complete": bundle["complete"], "bundle_limits": bundle["known_limits"], "export_limits": exported["knownLimits"], "manifest_limits": bundle["manifest"]["known_limits"], "verification_status": bundle["manifest"]["verification_status"]},
        "excluded_bodies": ["admission.envelope.input", "definition.goal", "job.input", "job.latestText", "job.result", "observation.payload.descriptor"],
        "results": records,
        "required_negative_cases": ["operator must not gain fake native agent/session", "reserved fields must not imply observed runtime existence", "native OrgTask must not alias bundle task/job", "Pi session must not alias OrgSession", "material binding field changes invalidate applicability", "ACK-loss attempted events must not multiply logical handovers", "manifest incomplete/UNKNOWN must survive bundle complete=true", "unknown/tied order must not become event-ID or invented microsecond order"]
    }
    (output / "binding-oracle.json").write_text(json.dumps(oracle, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"counts": oracle["counts"], "results": {k:v["status"] for k,v in records.items()}, "manifest_limits": oracle["coverage"]["manifest_limits"]}, indent=2))


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
