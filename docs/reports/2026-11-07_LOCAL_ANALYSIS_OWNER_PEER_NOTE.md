# PIX owner peer note: local metadata analysis — 2026-11-07

## Scope and inspected sources

This is computation-owner coordination, not a duplicate independent review or
authorization to read arbitrary private stores. PIX engine source and pins are
unchanged. Only PIX-owned notes and metadata fixtures are added.

The inspected Schumpeter port is `src/schumpeter/local_analysis.py`, source
commit `b900ef494c61b4840640c2bed2a44541f23cfe80`, evidence freeze
`6f0bb692110dbed871e98dbc0916c12a1930fe7a`. Its source SHA-256 is
`d49c468d01984cee28b8e28db0880abf1bbb53307b725a83e6fb1b7ddb10f700`.
Implementation, focused tests, report and native proof were read, not rerun by
this owner. The actual local-private fixture declares its real storage scope;
it is not private/live data relabelled as synthetic. It retains source event IDs,
journal positions, source revision digests and current grant identity. Revisions
remain in a hashed applicability sidecar rather than being falsely claimed as
fully encoded in native OCEL.

The proposed separate Pida port is owned by
`/root/schumpeter_owner/local_analysis`: registered PidaHost + admission authority
+ reservation ID, current source-specific approval, actual producer validator and
exporter, and rechecked native receipt/job/organization metadata. At this note's
creation no new `local_analysis_pida.py` draft was available for code inspection.
The advice below initially reviewed that declared contract direction. Before
freezing this note a draft became available, and was read at checkout HEAD
`00677fffef13f1d6d471093eb58e55015f0cdc38` (the module was still uncommitted).
Its exact bytes are bound by the peer manifest. It checks native root task,
attempt, receipt, job, run and session identities, retains all three coverage
domains, and selects the public operators described below. Its public adapter
`analysis_source` dependency and developer execution were not verified in this
peer slice. This is source-level semantic feedback, not implementation acceptance.

## Public PIX call selection

The existing CollaborationStore port selects public trace/DFG/OCDFG operators
with rejected timestamp ties, task-only execution extraction and exact variants.
Native statuses, issues and parent artifacts are retained. It does not fit a
reference model to its own observations and label the resulting cost a score.
No contrary computation finding was identified in the inspected source.

For actual Pida Run metadata use the explicit, existing profiles:

```python
spec = TraceSpec("Run", qualifiers=("run",), tie_policy="reject")
traces = reconstruct_traces(log, spec)
dfg = discover_dfg(log, spec)
executions = discover_executions(log, ExecutionSpec(
    "connected_components", object_types=("Run",), qualifiers=("run",),
    tie_policy="reject"))
variants = discover_variants(executions, VariantSpec())
```

`discover_ocdfg(log, OCDFGSpec(explicit_types, tie_policy="reject"))` is also
available for explicitly chosen typed layers; keep their object/event occurrence
counts separate. O2O relations do not invent DFG or execution connectivity.
Ties can make sequential results unavailable while source/event counts remain
known. Journal sequence is evidence of observation order, not permission to add
microtimestamps or event-ID causality. An arbitrary exact live object-cut
conformance profile is still not supplied by these operators.

## Concrete owner fixture and results

The [metadata oracle](evidence/local-analysis-peer-20261107/oracle/binding-oracle.json)
is derived directly from frozen Schumpeter adapter commit
`81c8a9485b2ca0df9bb9c971e45b90107aa25e94`. All three input artifacts match that
Git object's bytes. The [small peer probe](evidence/local-analysis-peer-20261107/binding_oracle.py)
reads those Git blobs and runs unmodified PIX public APIs; it makes no runtime,
network or model call. It does not copy admission input/goal, job input/output,
or Persona descriptor bodies. Its actual metadata-only OCEL and four native
result artifacts are next to the oracle.

This source was an **actual scripted mock runtime**, with neither real model
calls nor multiple agents executed. Its native root contains 16 events, 9
objects, 84 E2O and 11 O2O relations. All 16 timestamps are distinct; per-run
sequence is 1–16. Run traces, DFG, execution extraction and variants compute.
The Run DFG has 12 distinct activity edges and 15 observed edge occurrences,
checked independently against adjacent source activities. Native roundtrips and
parent artifact resolution pass. These results do not accept the future local
Pida port or desktop integration.

Exact join checks in that fixture:

| Meaning | Preserved relationship |
| --- | --- |
| Native job | `receipt.job_id == job.id == bundle.manifest.task_id` (`9c4a9131-417f-49f1-b8dd-4039f483c62d`) |
| Native organization task | `receipt.root_task_id == job.organizationTaskId` (`074f8994-2359-4510-84ed-01095741ae27`), distinct from job/runtime task |
| Native attempt | `receipt.root_attempt_id == job.attemptId` (`80d2e621-3f6b-4a19-8f63-0a95ec99db43`) |
| Native agent | Receipt recipient, observed binding, job and all bundle events agree on `034294ec-1559-4c47-8c30-ee65df3cafeb` |
| Pi session/run | Job and exported bundle agree; Pi session `01a1b610-9b72-74ff-aa37-3662ae9ac2cd` is distinct from native organization session `c2bfc83e-1f64-443e-b9cf-68d800df5810` |
| Operator sender | Explicit `kind=operator`, principal/organization/revision; no invented native agent/host/session fields |
| Observed recipient | Full persistent organization, host, native organization session, agent and binding revision, supplied after `organization_admission_observed` / `native_readback` |

Reservation fields are proposed IDs, not runtime-existence evidence. A durable
`organization_root_enqueued` receipt is not context consumption, execution or
acceptance. This trace's `complete=true` and empty bundle limits coexist with
manifest `EVIDENCE_OR_STORAGE_INCOMPLETE`, UNKNOWN acceptance, unconfirmed
artifact state, unknown cost and other limits. The proposed port must preserve
bundle, exporter, manifest and native result coverage separately.

## Required sidecar and applicability rules

The trusted embedding supplies owner/principal scope; a sender/model body must
not authenticate it. Preserve that scope plus producer/request/recipient carrier
identity, exact receipt byte hash and phase, payload/definition/admission digests,
reservation/source IDs, room/contract revisions, operator or native sender kind,
full observed recipient binding, and exact native execution joins above.

Record original source event IDs, source sequence domain and times separately
from projected native IDs. Source revision/exporter/model/spec/build/grant and
binding changes must invalidate applicability or produce a new analysis identity,
even when numerical counts coincide. Re-resolve current access and exact source
selection before publishing or serving prior evidence. A registered source plus
its source-specific approval is not arbitrary-path import permission.

Actual producer validation/export may consume the original bundle transiently,
but persist only the reviewed metadata vocabulary and hashes. Retain descriptor
or model-input receipt references/digests only; never save their body, the
admission envelope input, goal, job text or Persona content in this local
metadata profile. Metadata remains private and local; no upload is authorized.
The inspected Pida draft relies on actual producer closed-schema validation
before omitting event payloads. The current manifest vocabulary contains revision
and verification metadata. A future schema expansion must not silently expand
metadata-only permission; source/tool hashes need to bind the reviewed vocabulary.

The local port's imported package-source hash and executable hash are useful
observations. They are not proof of loaded bytecode or a verified Git commit.
Frozen Git identity must remain null/unverified where not established. Packaged
source inventories should be checked against the running artifact and then the
actual frozen invocation exercised before a packaged-profile claim. Adding a
new module to a build manifest alone does not perform that acceptance.

## Handover conditions

Existing local CollaborationStore `message.post` / `message.receipt` can use
qualified message `sent` / `received` with organization `sender` / `recipient`
and declared precision. The current local port conservatively skips handover
without a matched carrier pair; that is an availability policy, not evidence
that traffic is absent. PIX can retain unmatched sends/receives when a valid
qualified carrier/actor schema is supplied.

For the proposed native Pida Run profile, **handover unavailable is correct**.
This OCEL has no organization/message carrier projection. The admission sidecar
has two `admission_attempted` observations for one ACK-loss deduplicated first
root; they must not become two logical sends. Native handover enumerates observed
send/receive combinations sharing a carrier; it is not a retry-dedup engine.
Keep attempts, queue receipt and binding-readback facts distinct until a reviewed
logical-message carrier projection explicitly relates them. Do not assign an
operator a fake agent identity or infer cross-run causal ordering.

## Next validation and withdrawal

The owner shared this fixture, public calls and eight concrete negative cases
with the Schumpeter local-analysis owner. The next unit is its actual new
registered-source implementation: verify source/binding changes, revoked access,
wrong native job/task/attempt/session, missing readback, operator/native separation,
timestamp ties and incomplete coverage against these fixtures. Independent
review and actual frozen invocation are separate gates.

The [earlier actual single-model trace analysis](2026-11-07_ACTUAL_PIDA_TRACE_INVESTIGATION.md)
also passed a separate independent read-only review. Its
[verbatim record](evidence/live-pida-smoke-20261107/independent-review/REVIEW.md)
and [artifact check](evidence/live-pida-smoke-20261107/independent-review/artifact-verification.json)
are preserved with hashes in the peer manifest. That review did not rebuild the
compiled exporter, reobserve the historical model call, or accept this new port.

Withdraw the proposed contract assessment if material lineage is dropped, source
scope is relabelled, operator intent becomes native execution, missing/tied order
is repaired, a native/manifest limit is erased, or a different binding/build/grant
can reuse old applicability. Validity is limited to the cited source and proposed
profile semantics. Organizational improvement is **알 수 없음**; leaving current
descriptive analysis unchanged remains viable while required source evidence is
unavailable.

Conclusion: **owner peer PASS for the inspected local calculation choices and
proposed bounded Run metadata direction and draft computation semantics**; the new Pida implementation, trusted
receipt binding enforcement and frozen desktop acceptance remain unreviewed here.
