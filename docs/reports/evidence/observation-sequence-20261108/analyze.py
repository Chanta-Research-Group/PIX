"""Exact native-sequence projection of one approved saved metadata run.

No offset normalization, fabricated start/end event, OCEL edit or workload.
"""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
from pix.case_centric.stream_adapters import RecordStreamSpec, StreamRecord, records_stream, consume_stream_batch
from pix.case_centric.streaming import StreamingSpec
from pix.results import read_result, result_json_bytes, write_result

ENGINE = "6e9af5ee1b670de39a87be406518fea49dffdfec"
PROFILE = "pix.owner.observation-sequence-run/1"
STRICT = HERE.parent / "repository-persona-20261108"
SOURCE = STRICT / "native/approved-source"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def attrs(item):
    return {a["name"]: a["value"] for a in item["attributes"]}


def validated_rows(document, manifest, identity):
    assert manifest["task_id"] == identity["job_id"]
    for key in ("run_id", "session_id", "agent_id"):
        if manifest[key] != identity[key]:
            raise ValueError("manifest_domain_mismatch")
    expected = {"Run": ("run_id", identity["run_id"]), "Session": ("session_id", identity["session_id"]),
                "Task": ("task_id", identity["job_id"]), "Agent": ("agent_id", identity["agent_id"])}
    objects = {}
    for kind, (key, value) in expected.items():
        selected = [o for o in document["objects"] if o["type"] == kind]
        if len(selected) != 1 or attrs(selected[0]).get(key) != value:
            raise ValueError("native_object_domain_mismatch")
        objects[kind] = selected[0]["id"]
    rows = []
    for e in document["events"]:
        a = attrs(e)
        sequence = a.get("sequence_number")
        if type(sequence) is not int or sequence < 1:
            raise ValueError("native_sequence_required_positive_integer")
        relations = {(r["objectId"], r["qualifier"]) for r in e["relationships"]}
        if not {(objects[t], q) for t,q in (("Run", "run"), ("Session", "session"), ("Task", "task"), ("Agent", "actor"))} <= relations:
            raise ValueError("event_domain_relationship_mismatch")
        rows.append({"source_id": a["source_id"], "source_event_id": a["source_event_id"],
            "ocel_event_id": e["id"], "native_sequence": sequence, "activity": e["type"],
            "timestamp": e["time"], "payload_digest": a["payload_digest"], "relationships": e["relationships"]})
    if not rows or len({r["source_id"] for r in rows}) != 1:
        raise ValueError("ambiguous_source_sequence_domain")
    if len({r["source_event_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate_source_event_id")
    rows.sort(key=lambda r: r["native_sequence"])
    if [r["native_sequence"] for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("noncontiguous_or_duplicate_native_sequence")
    if rows[0]["activity"] != "run_started" or rows[-1]["activity"] != "run_finished":
        raise ValueError("declared_full_run_cut_unavailable")
    return rows


def run(output):
    output = Path(output)
    subprocess.run(["git", "diff", "--exit-code", ENGINE, "--", "src/pix", "pyproject.toml"], cwd=ROOT, check=True)
    handoff = json.loads((SOURCE / "handoff.json").read_bytes())
    identity = next(r for r in handoff["records"] if r["files"].get("sdk-profile-a.ocel.json"))
    assert identity["status"] == "failed" and identity["code"] == "PROGRAM_EXIT_FAILED"
    input_hashes = {name:sha(SOURCE/name) for name in identity["files"]}
    assert input_hashes == identity["files"]
    strict_before = {p.relative_to(STRICT).as_posix():sha(p) for p in (STRICT / "native").rglob("*.json")}
    document = json.loads((SOURCE / "sdk-profile-a.ocel.json").read_bytes())
    manifest = json.loads((SOURCE / "sdk-profile-a.manifest.json").read_bytes())
    meta = json.loads((SOURCE / "sdk-profile-a.ocel.meta.json").read_bytes())
    assert meta["complete"] is True and manifest["verification_status"] == "UNKNOWN"
    rows = validated_rows(document, manifest, identity)
    domain = {"source_id": rows[0]["source_id"], "session_id": identity["session_id"], "run_id": identity["run_id"]}
    case_id = json.dumps(domain, sort_keys=True, separators=(",", ":"))
    namespace = PROFILE + ":" + input_hashes["sdk-profile-a.ocel.json"]
    records = [StreamRecord(case_id, r["source_event_id"], r["activity"],
               datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")), r["native_sequence"]) for r in rows]
    spec = RecordStreamSpec(namespace, order_policy="sequence", duplicate_policy="reject",
                            close_cases=False, start_sequences=((case_id, 1),), max_events=len(rows))
    batch = records_stream(records, spec)
    assert batch.status.value == "computed"
    for original, projected, occurrence in zip(rows, batch.value.events, batch.value.occurrences, strict=True):
        assert projected.sequence == original["native_sequence"]
        assert projected.timestamp == datetime.fromisoformat(original["timestamp"].replace("Z", "+00:00"))
        assert occurrence.source_event_id == original["source_event_id"]
        assert projected.activity == original["activity"]
        assert not projected.end and not occurrence.synthetic_end
    stream_spec = StreamingSpec(namespace, order_policy="sequence", max_cases=1,
                                max_activities=len({r["activity"] for r in rows}), dedup_window=len(rows))
    delivery = consume_stream_batch(batch, stream_spec)
    assert delivery.status.value == "unavailable" and delivery.value is None
    assert any("a new case must start at sequence zero" in issue.message for issue in delivery.issues)
    # Negative mapping probes are isolated synthetic copies; original OCEL bytes are never changed.
    negatives = {}
    for name in ("absent", "duplicate", "fractional", "boolean", "domain", "source_event_conflict", "cut_gap"):
        invalid = deepcopy(document)
        seq = next(a for a in invalid["events"][1]["attributes"] if a["name"] == "sequence_number")
        if name == "absent": invalid["events"][1]["attributes"].remove(seq)
        elif name == "duplicate": seq["value"] = 1
        elif name == "fractional": seq["value"] = 1.5
        elif name == "boolean": seq["value"] = True
        elif name == "domain": next(a for a in invalid["events"][1]["attributes"] if a["name"] == "source_id")["value"] = "synthetic-other-domain"
        elif name == "source_event_conflict": next(a for a in invalid["events"][1]["attributes"] if a["name"] == "source_event_id")["value"] = attrs(invalid["events"][0])["source_event_id"]
        elif name == "cut_gap": invalid["events"].pop(1)
        try:
            validated_rows(invalid, manifest, identity)
        except ValueError as exc:
            negatives[name] = str(exc)
        else:
            raise AssertionError("negative accepted: " + name)
    output.mkdir(parents=True, exist_ok=False)
    result_rows = {}
    for name, result in (("record-projection", batch), ("sequence-delivery", delivery)):
        path = output / (name + ".json")
        write_result(result, path)
        assert result_json_bytes(read_result(path)) == path.read_bytes()
        result_rows[name] = {"status": result.status.value, "sha256":sha(path), "computation_id":result.computation_id,
            "source_digest":result.source_digest, "parents":list(result.parent_computation_ids), "issues":[asdict(i) for i in result.issues]}
    assert delivery.parent_computation_ids == (batch.computation_id,)
    strict_after = {p.relative_to(STRICT).as_posix():sha(p) for p in (STRICT / "native").rglob("*.json")}
    assert strict_before == strict_after
    record = {"schema":PROFILE, "engine_pin":ENGINE, "python":sys.version, "script_sha256":sha(__file__),
        "provenance":"derived per-run observation/case view; not native OCEL/OCPM replacement, causal or efficiency proof",
        "input_hashes":input_hashes, "original_handoff_sha256":sha(SOURCE/'handoff.json'), "native_identity":identity,
        "domain":domain, "case_id":case_id, "mapping":rows, "record_spec":asdict(spec), "stream_spec":asdict(stream_spec),
        "declared_cut":{"first_sequence":1,"last_sequence":len(rows),"events":len(rows),"source_complete":meta["complete"],
                        "logical_source_terminal":"run_finished retained as original activity; no synthetic close"},
        "results":result_rows, "negative_mapping_probes":negatives,
        "strict_native_tree_before_after":strict_before, "source_manifest":manifest, "export_meta":meta,
        "snapshot_atomic":False, "coverage":"partial; exact single-run saved observations only",
        "limitation":"RecordStreamSpec preserves native 1-based sequence; CaseStream requires new case sequence0. Delivery unavailable. No renumbering performed.",
        "next_contract_option":"Review an explicit separate zero-based delivery index while retaining immutable native sequence in provenance, or separately review generic stream start-offset support. Neither is applied here."}
    (output/'run-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({"projection":batch.status.value,"delivery":delivery.status.value,"events":len(rows),
        "native_sequence_range":[1,len(rows)],"negative_mapping_probes":len(negatives),"strict_files_unchanged":len(strict_before),
        "delivery_issues":[i.message for i in delivery.issues]},indent=2))


if __name__ == "__main__":
    run(sys.argv[1])
