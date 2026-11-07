"""Independent, approved metadata-only audit; no workload or original writes."""
from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from datetime import datetime

ROOT=Path('D:/ChantaResearchGroup/PIX-transport-review-20261108')
OUT=Path(__file__).resolve().parent
REL='docs/reports/evidence/'
TRAN=ROOT/REL/'observation-transport-20261108'
STRICT=ROOT/REL/'repository-persona-20261108'
EXACT=ROOT/REL/'observation-sequence-20261108'
SRC=STRICT/'native/approved-source'
PIN='cba1dc185846338eeeb839645a7a1a1071924692'
EPIN='cb0917ca3c1b14582474a436b9a69d596816083c'
SPIN='e36d7864f64c1a979ef612a31084eb62c89d3702'
ENGINE='6e9af5ee1b670de39a87be406518fea49dffdfec'
sha=lambda b: hashlib.sha256(b).hexdigest()
read=lambda p: json.loads(p.read_bytes())
git=lambda *a: subprocess.check_output(['git','-C',str(ROOT),*a])
assert git('rev-parse','HEAD').decode().strip()==PIN
assert not git('diff',ENGINE,'--','src/pix','pyproject.toml')
checked={}
for folder,pin in ((STRICT,SPIN),(EXACT,EPIN),(TRAN,PIN)):
    for p in folder.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts: continue
        relative=p.relative_to(ROOT).as_posix()
        assert p.read_bytes()==git('show',pin+':'+relative), relative
        checked[relative]=sha(p.read_bytes())
for folder in (STRICT,TRAN):
    for relative,digest in read(folder/'source-manifest.json')['files'].items():
        assert sha((ROOT/relative).read_bytes())==digest,relative
prior=read(TRAN/'native/run-record.json')['checks']['prior_artifact_hashes_unchanged']
assert len(prior)==92
for relative,digest in prior.items(): assert sha((ROOT/relative).read_bytes())==digest
upstream={}
for name in ('handoff.json','sdk-profile-a.ocel.json','sdk-profile-a.ocel.meta.json','sdk-profile-a.manifest.json'):
    path='docs/development/repository-catalogue-combination-evidence-20261108/metadata-only/'+name
    blob=subprocess.check_output(['git','-C','D:/ChantaResearchGroup/pida-repository-profile-20261108','show','ff68457f7d032bfa0aa81badf27bdf4079cadc5e:'+path])
    assert blob==(SRC/name).read_bytes()
    upstream[path]=sha(blob)

spec=importlib.util.spec_from_file_location('reviewed_transport',TRAN/'project.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from pix.results import read_result,result_json_bytes
from pix.case_centric.stream_adapters import records_stream,RecordStreamSpec,consume_stream_batch
from pix.case_centric.streaming import StreamingSpec
owner=read(TRAN/'native/run-record.json')
reproduced=read(OUT/'reproduced/run-record.json')
assert owner==reproduced
for sub,folder in (('reproduced',TRAN),('exact-reproduced',EXACT)):
    for name in ('record-projection','sequence-delivery'):
        p=OUT/sub/(name+'.json')
        assert p.read_bytes()==(folder/'native'/p.name).read_bytes()
        assert result_json_bytes(read_result(p))==p.read_bytes()

document=read(SRC/'sdk-profile-a.ocel.json')
manifest=read(SRC/'sdk-profile-a.manifest.json')
identity=owner['native_identity']
attr=lambda item:{a['name']:a['value'] for a in item['attributes']}
events=sorted(document['events'],key=lambda e:attr(e)['sequence_number'])
assert [attr(e)['sequence_number'] for e in events]==list(range(1,17))
assert len({e['id'] for e in events})==16
assert len({attr(e)['source_event_id'] for e in events})==16
domain=owner['mapping_policy']['domain']
for kind,key in (('Run','run_id'),('Session','session_id'),('Task','task_id'),('Agent','agent_id')):
    obj=next(o for o in document['objects'] if o['type']==kind)
    assert attr(obj)[key]==identity['job_id' if key=='task_id' else key]
    qualifier={'Run':'run','Session':'session','Task':'task','Agent':'actor'}[kind]
    assert all({'objectId':obj['id'],'qualifier':qualifier} in e['relationships'] for e in events)
for i,(event,row) in enumerate(zip(events,owner['records'],strict=True)):
    a=attr(event)
    assert (row['native_sequence'],row['transport_sequence'])==(i+1,i)
    assert row['transport_sequence']+1==a['sequence_number']
    assert row['ocel_event_id']==event['id'] and row['source_event_id']==a['source_event_id']
    assert row['source_id']==a['source_id']==domain['source_id']
    assert row['timestamp']==event['time'] and row['activity']==event['type']
    assert row['relationships']==event['relationships'] and row['payload_digest']==a['payload_digest']
assert domain['run_id']==identity['run_id'] and domain['session_id']==identity['session_id']
assert events[1]['time']==events[2]['time']=='2026-11-07T18:34:21.847Z'
assert Counter(zip([e['type'] for e in events],[e['type'] for e in events][1:]))=={(a,b):n for a,b,n in owner['observations']['dfg_edges']}

rows=module.contract.validated_rows(document,manifest,identity)
negative={}
for name in ('absent','duplicate','fractional','boolean','domain','event_id','gap','wrong_declared_start'):
    bad=deepcopy(rows);first=1
    if name=='absent': bad[2].pop('native_sequence')
    elif name=='duplicate': bad[2]['native_sequence']=2
    elif name=='fractional': bad[2]['native_sequence']=2.5
    elif name=='boolean': bad[2]['native_sequence']=False
    elif name=='domain': bad[-1]['source_id']='review-other-source'
    elif name=='event_id': bad[-1]['source_event_id']=bad[0]['source_event_id']
    elif name=='gap': bad.pop(-1)
    else: first=2
    try: module.transport(bad,domain,first,16)
    except ValueError as exc: negative[name]=str(exc)
    else: raise AssertionError(name)
domain_negative={}
for name in ('manifest_run','manifest_session','object_run','object_session','event_relation'):
    doc=deepcopy(document);man=deepcopy(manifest)
    if name.startswith('manifest_'): man[name[9:]+'_id']='review-other'
    elif name.startswith('object_'):
        typ=name[7:].title();obj=next(o for o in doc['objects'] if o['type']==typ)
        next(a for a in obj['attributes'] if a['name']==name[7:]+'_id')['value']='review-other'
    else: doc['events'][-1]['relationships']=[r for r in doc['events'][-1]['relationships'] if r['qualifier']!='run']
    try: module.contract.validated_rows(doc,man,identity)
    except ValueError as exc: domain_negative[name]=str(exc)
    else: raise AssertionError(name)
assert module.transport(list(reversed(rows)),domain,1,16)==owner['records']
rspec=RecordStreamSpec(owner['record_spec']['namespace'],order_policy='sequence',duplicate_policy='reject',close_cases=False,sequence_key='transport_sequence',start_sequences=((module.canonical(domain),0),),max_events=16)
native=lambda rr:[{**r,'timestamp':datetime.fromisoformat(r['timestamp'].replace('Z','+00:00'))} for r in rr]
batch=records_stream(native(owner['records']),rspec)
assert batch.computation_id==owner['results']['record-projection']['computation_id']
identity_checks={}
for field,value in (('native_sequence',999),('payload_digest','review-other'),('ocel_event_id','review-other')):
    changed=deepcopy(owner['records']);changed[0][field]=value
    result=records_stream(native(changed),rspec)
    assert result.source_digest!=batch.source_digest and result.computation_id!=batch.computation_id
    identity_checks[field]=True
for field,value in (('handoff_sha256','review-other'),('profile','review.other/1'),('declared_last_native_sequence',17)):
    policy={**owner['mapping_policy'],field:value}
    namespace=module.PROFILE+':'+sha(module.canonical(policy).encode())
    result=records_stream(native(owner['records']),replace(rspec,namespace=namespace))
    assert result.computation_id!=batch.computation_id
    identity_checks['policy_'+field]=True
assert all(not e.end for e in batch.value.events)
delivery=read_result(OUT/'reproduced/sequence-delivery.json')
assert delivery.parent_computation_ids==(batch.computation_id,)
assert delivery.status.value=='partial' and any(i.code=='open_cases' for i in delivery.issues)
assert delivery.value.checkpoint.snapshot.closed_cases==0
strict_native=[]
for p in (STRICT/'native').rglob('*.json'):
    if 'approved-source' in p.parts or p.name=='run-record.json': continue
    try: result=read_result(p)
    except Exception: continue
    assert result_json_bytes(result)==p.read_bytes()
    strict_native.append({'path':p.relative_to(ROOT).as_posix(),'status':result.status.value,'sha256':sha(p.read_bytes())})
assert len(strict_native)==68,len(strict_native)
assert Counter(r['status'] for r in strict_native)=={'computed':58,'unavailable':10}
assert manifest['reported_status']=='failed' and manifest['code']=='PROGRAM_EXIT_FAILED'
assert manifest['verification_status']=='UNKNOWN' and owner['snapshot_atomic'] is False
assert not git('status','--porcelain')
summary={'reviewed_commit':PIN,'engine_commit':ENGINE,'python':sys.version,'approved_upstream':upstream,'checked_pinned_files':checked,'prior_files_unchanged':92,'strict_native_results':strict_native,'transport_owner_record_exact_equal':True,'two_native_results_byte_equal':True,'exact_one_based_failure_reproduced':True,'events':16,'native_range':[1,16],'transport_range':[0,15],'negative_mapping_checks':negative,'negative_domain_checks':domain_negative,'identity_mutation_checks':identity_checks,'domain':domain,'partial_open_no_synthetic_closure':True,'source_failure_retained':True,'scope':'one pinned approved failed SDK metadata run; no engine change, private raw access, live workloads or Sch adoption'}
(OUT/'audit.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'checked_files':len(checked),'prior_files':92,'strict_outputs':68,'independent_negative_checks':len(negative)+len(domain_negative),'identity_mutations':len(identity_checks),'audit_sha256':sha((OUT/'audit.json').read_bytes())},indent=2))
