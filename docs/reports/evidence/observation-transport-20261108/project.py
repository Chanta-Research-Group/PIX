"""Explicit invertible transport index over one immutable approved native run."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXACT = HERE.parent / "observation-sequence-20261108"
STRICT = HERE.parent / "repository-persona-20261108"
SOURCE = STRICT / "native/approved-source"
ENGINE = "6e9af5ee1b670de39a87be406518fea49dffdfec"
PROFILE = "pix.owner.native-sequence-transport/1"
VALIDATOR_COMMIT = "cb0917ca3c1b14582474a436b9a69d596816083c"
validator_path = EXACT / "analyze.py"
assert validator_path.read_bytes() == subprocess.check_output([
    "git", "-C", str(ROOT), "show", VALIDATOR_COMMIT + ":" + validator_path.relative_to(ROOT).as_posix()])
module_spec = importlib.util.spec_from_file_location("exact_sequence_contract", validator_path)
contract = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(contract)
from pix.case_centric.stream_adapters import RecordStreamSpec, records_stream, consume_stream_batch
from pix.case_centric.streaming import StreamingSpec
from pix.results import read_result, result_json_bytes, write_result


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def transport(rows, domain, declared_first, declared_last):
    if type(declared_first) is not int or type(declared_last) is not int:
        raise ValueError("invalid_declared_cut")
    if not rows or any(type(r.get("native_sequence")) is not int for r in rows):
        raise ValueError("native_sequence_required_integer")
    if any(r["source_id"] != domain["source_id"] for r in rows):
        raise ValueError("mixed_domain")
    rows = sorted(rows, key=lambda r:r["native_sequence"])
    if [r["native_sequence"] for r in rows] != list(range(declared_first, declared_last + 1)):
        raise ValueError("declared_cut_mismatch_or_gap_or_duplicate")
    if len({r["source_event_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate_event_identity")
    case_id = canonical(domain)
    result = [{**r, "case_id":case_id, "event_id":r["source_event_id"],
               "transport_sequence":r["native_sequence"] - declared_first} for r in rows]
    assert all(r["transport_sequence"] + declared_first == r["native_sequence"] for r in result)
    return result


def run(output):
    output = Path(output)
    subprocess.run(["git", "diff", "--exit-code", ENGINE, "--", "src/pix", "pyproject.toml"], cwd=ROOT, check=True)
    original = {str(p.relative_to(ROOT)):sha(p) for folder in (STRICT, EXACT) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    handoff = json.loads((SOURCE/'handoff.json').read_bytes())
    identity = next(r for r in handoff['records'] if 'sdk-profile-a.ocel.json' in r['files'])
    assert all(sha(SOURCE/name)==h for name,h in identity['files'].items())
    document = json.loads((SOURCE/'sdk-profile-a.ocel.json').read_bytes())
    manifest = json.loads((SOURCE/'sdk-profile-a.manifest.json').read_bytes())
    meta = json.loads((SOURCE/'sdk-profile-a.ocel.meta.json').read_bytes())
    assert meta['complete'] is True and manifest['reported_status']=='failed' and manifest['code']=='PROGRAM_EXIT_FAILED'
    rows = contract.validated_rows(document, manifest, identity)
    domain = {'source_id':rows[0]['source_id'], 'session_id':identity['session_id'], 'run_id':identity['run_id']}
    declared_first, declared_last = 1, 16
    mapped = transport(rows, domain, declared_first, declared_last)
    mapping_policy = {'profile':PROFILE, 'domain':domain, 'declared_first_native_sequence':declared_first,
        'declared_last_native_sequence':declared_last, 'formula':'transport_sequence = native_sequence - declared_first_native_sequence',
        'inverse':'native_sequence = transport_sequence + declared_first_native_sequence',
        'handoff_sha256':sha(SOURCE/'handoff.json'), 'ocel_sha256':sha(SOURCE/'sdk-profile-a.ocel.json'),
        'original_native_sequence_unchanged':True, 'timestamp_order_policy':'not used for adjacency; original time retained'}
    policy_digest = hashlib.sha256(canonical(mapping_policy).encode()).hexdigest()
    namespace = PROFILE + ':' + policy_digest
    case_id = canonical(domain)
    spec = RecordStreamSpec(namespace, order_policy='sequence', duplicate_policy='reject', close_cases=False,
                            sequence_key='transport_sequence', start_sequences=((case_id, 0),), max_events=len(mapped))
    def native_records(items):
        return [{**r, 'timestamp':datetime.fromisoformat(r['timestamp'].replace('Z','+00:00'))} for r in items]
    batch = records_stream(native_records(mapped), spec)
    assert batch.status.value=='computed'
    for item,event,occurrence in zip(mapped,batch.value.events,batch.value.occurrences,strict=True):
        assert event.sequence==item['transport_sequence'] and event.sequence+declared_first==item['native_sequence']
        assert event.timestamp==datetime.fromisoformat(item['timestamp'].replace('Z','+00:00'))
        assert occurrence.source_event_id==item['source_event_id'] and occurrence.source_case_id==case_id
        assert event.activity==item['activity'] and not event.end and not occurrence.synthetic_end
    stream_spec=StreamingSpec(namespace,order_policy='sequence',max_cases=1,max_activities=len({r['activity'] for r in mapped}),dedup_window=len(mapped))
    delivery=consume_stream_batch(batch,stream_spec)
    assert delivery.status.value=='partial' and delivery.value is not None
    state=delivery.value.checkpoint.snapshot
    assert state.accepted_events==16 and state.accepted_operations==16 and state.created_cases==1 and state.closed_cases==0
    assert len(state.cases)==1 and not state.cases[0].closed and state.cases[0].last_sequence==15
    word=[r['activity'] for r in mapped]
    expected_edges=Counter(zip(word,word[1:]))
    assert {(a,b):n for a,b,n in state.dfg.edges}==expected_edges
    assert dict(state.dfg.activities)==Counter(word) and not state.dfg.ends
    assert any(i.code=='open_cases' for i in delivery.issues)
    # Explicit synthetic negative mapping probes; none changes an input artifact.
    negatives={}
    for name in ('absent','duplicate','fractional','boolean','domain','event_id','gap','wrong_declared_start'):
        broken=deepcopy(rows); start=declared_first
        if name=='absent': broken[1].pop('native_sequence')
        elif name=='duplicate': broken[1]['native_sequence']=1
        elif name=='fractional': broken[1]['native_sequence']=1.5
        elif name=='boolean': broken[1]['native_sequence']=True
        elif name=='domain': broken[1]['source_id']='synthetic-different-domain'
        elif name=='event_id': broken[1]['source_event_id']=broken[0]['source_event_id']
        elif name=='gap': broken.pop(1)
        elif name=='wrong_declared_start': start=0
        try: transport(broken,domain,start,declared_last)
        except ValueError as exc: negatives[name]=str(exc)
        else: raise AssertionError('invalid mapping accepted: '+name)
    assert transport(list(reversed(rows)),domain,declared_first,declared_last)==mapped
    # Extra native provenance is part of records_stream's source identity, not discarded metadata.
    altered=deepcopy(mapped); altered[0]['native_sequence']=999
    altered_batch=records_stream(native_records(altered),spec)
    assert altered_batch.source_digest!=batch.source_digest and altered_batch.computation_id!=batch.computation_id
    other_domain={**domain,'run_id':'synthetic-other-run'}
    assert canonical(other_domain)!=case_id
    assert hashlib.sha256(canonical({**mapping_policy,'domain':other_domain}).encode()).hexdigest()!=policy_digest
    output.mkdir(parents=True,exist_ok=False)
    results={}
    for name,result in (('record-projection',batch),('sequence-delivery',delivery)):
        path=output/(name+'.json');write_result(result,path)
        assert result_json_bytes(read_result(path))==path.read_bytes()
        results[name]={'status':result.status.value,'sha256':sha(path),'source_digest':result.source_digest,
            'computation_id':result.computation_id,'parents':list(result.parent_computation_ids),'issues':[asdict(i) for i in result.issues]}
    assert delivery.parent_computation_ids==(batch.computation_id,)
    assert all(sha(ROOT/path)==h for path,h in original.items())
    record={'schema':PROFILE,'engine_pin':ENGINE,'python':sys.version,'script_sha256':sha(__file__),
        'validator_commit':VALIDATOR_COMMIT,'validator_sha256':sha(validator_path),'mapping_policy':mapping_policy,
        'mapping_policy_digest':policy_digest,'records':mapped,'record_spec':asdict(spec),'stream_spec':asdict(stream_spec),
        'results':results,'native_identity':identity,'manifest':manifest,'export_meta':meta,
        'checks':{'invertible_all_events':True,'native_event_ids_times_sequences_preserved':True,'negative_probes':negatives,
            'reversed_delivery_same_projection_mapping':True,'native_provenance_changes_result_identity':True,'different_run_changes_domain_identity':True,
            'synthetic_end_markers':0,'prior_artifact_hashes_unchanged':original},
        'observations':{'events':state.accepted_events,'cases':state.created_cases,'closed_cases':state.closed_cases,
            'activity_counts':list(state.dfg.activities),'dfg_edges':list(state.dfg.edges),'dfg_distinct_edges':len(state.dfg.edges),
            'dfg_occurrences':sum(n for a,b,n in state.dfg.edges),'source_terminal':'failed / PROGRAM_EXIT_FAILED',
            'stream_scope':'open prefix because no synthetic closure was introduced'},
        'coverage':'partial single-run observation/case view; no atomic organization cut','snapshot_atomic':False,
        'not_claimed':['replacement of strict native OCEL/OCPM results','timestamp repair','cross-run order or causality','host project artifact capture','conformance or efficiency','model input body verification']}
    (output/'run-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'projection':batch.status.value,'delivery':delivery.status.value,'events':16,
        'native_sequence':[1,16],'transport_sequence':[0,15],'dfg_distinct_edges':len(state.dfg.edges),
        'dfg_occurrences':sum(n for a,b,n in state.dfg.edges),'negative_probes':len(negatives),'unchanged_prior_files':len(original)},indent=2))


if __name__=='__main__': run(sys.argv[1])
