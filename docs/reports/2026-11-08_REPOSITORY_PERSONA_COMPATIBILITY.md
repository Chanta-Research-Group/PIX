# Repository mode + external Persona metadata: existing PIX compatibility

## Scope and immutable sources

Only the explicitly approved metadata handoff from pida evidence commit
`ff68457f7d032bfa0aa81badf27bdf4079cadc5e` was consumed. Its
`handoff.json` SHA-256 is
`4863f97cf8169f722d901b6ff6d400c59540e80f1c0b5abfac5cb8075667cdac`.
All 13 approved handoff/OCEL/manifest files matched both recorded hashes and
the exact Git blob bytes. The approved adjacent producer report and verification
record were read; no raw bundle, supervisor state, Persona context, goal,
tool body, private store or synthetic temporary directory was opened.

Owner provenance identifies runtime/package source
`e9a1d31140bcff34e3c9ef0f82f4b3dbca0ddd68`, Persona source
`f6edd022d4389237fcee5d6c0a4db8a0d0b13399`, and Persona runtime digest
`0f85831175f24aea7237a6a003bdb14972a32cf13a7e76394c3fa9898b3763d6`.
Those are handed-off provenance claims, not a new package/store audit here.
Likewise, native OrgSession/OrgTask/attempt and selected Persona identifiers are
trusted owner-sidecar joins; only their consistency and preservation were checked.
Private source-state hashes were retained without reopening the source state.

Two inputs came from actual stock mock-host goals. Two came from the public SDK
with a scripted provider and simulated 15-token response usage. These are four
existing final Windows traces, not real-provider calls or a new combined
multi-agent/delegation test. The stock/SDK distinction remains on every run row.

PIX source under `src/pix` and `pyproject.toml` exactly matches requested engine
`6e9af5ee1b670de39a87be406518fea49dffdfec`. No engine or pin changes were made.
Direct execution used Python 3.13.14 through uv and tzdata. The reproducible
[analyzer](evidence/repository-persona-20261108/analyze.py) invoked only existing
PIX public APIs against copied approved OCEL. No new exporter, provider, workload,
account or GUI operation ran.

## Direct per-run results

Each run was imported separately. Typed traces/DFGs and OCDFG use
`tie_policy="reject"`; execution extraction uses connected components selected
by `Run` with qualifier `run`; variants consume that native execution result.

| Exact handoff component | Reported runtime state | Events / objects | E2O / O2O | Native outputs | Run DFG |
| --- | --- | --- | --- | --- | --- |
| stock-profile-a | completed | 16 / 9 | 84 / 11 | 17 computed | 12 distinct edges, 15 occurrences |
| stock-profile-b | completed | 16 / 9 | 84 / 11 | 17 computed | 12 distinct edges, 15 occurrences |
| sdk-profile-a | failed, PROGRAM_EXIT_FAILED | 16 / 9 | 84 / 11 | 7 computed, 10 unavailable | unavailable: ambiguous event order |
| sdk-profile-b | completed, separate repaired goal | 30 / 15 | 164 / 21 | 17 computed | 12 distinct edges, 29 occurrences |

These are per-run counts, not organization/company totals or an efficiency
comparison. All 68 result artifacts serialized and roundtripped exactly; every
parent computation reference resolves within the respective run's captured
results. For available Run DFGs, edge occurrence counts independently match
adjacent original timestamp-ordered activity labels.

The failed SDK run has one original timestamp tie at
`2026-11-07T18:34:21.847Z`:

- Sequence 2, `context_snapshot_loaded`, source event
  `0fe29cf8-b599-4c2f-96b8-dca52387f9ba`.
- Sequence 3, `run_context_loaded`, source event
  `fba8484b-1e39-439a-bf26-d34423c2f36d`.

Agent/Run/Session/Task traces and DFGs, OCDFG and variants therefore remain
unavailable under the selected native strict-order profile. ModelRequest,
ToolCall and Turn traces/DFGs compute. Execution extraction computes but retains
`ambiguous_event_order`; it does not claim a known total order. No artificial
microseconds or sequence-based causal ordering were introduced. Original event
IDs, OCEL IDs, source IDs, times and local sequence values were checked against
PIX's imported representation and saved in the result record. This is a supported
uncertainty result, not evidence requiring an engine repair.

## Existing observation-sequence alternative: inspected, not executed

PIX already has generic case-stream sequence support at the same engine revision:

- `src/pix/case_centric/stream_adapters.py`: `RecordStreamSpec` supports explicit
  `order_policy="sequence"`; `records_stream` requires sequence values and rejects
  non-unique/non-contiguous positions within each supplied case. Duplicate-event
  content conflicts fail; default duplicate policy is reject. `start_sequences`
  can enforce the declared first position.
- `src/pix/case_centric/streaming.py`: `StreamingSpec(order_policy="sequence")`
  and `consume_stream_batch` support native per-case observation sequence and
  streaming DFG facts. Ordering remains a declared projection convention, not
  causal evidence.
- `src/pix/event_log/adapters.py`: `case_traces` preserves explicit CaseLog source
  sequence. This is a case projection, not a switch on OCEL object traces.

By contrast, `src/pix/contracts/analysis.py` and `src/pix/compute/trace.py`
show that direct OCEL TraceSpec supports reject/event_id/concurrent over time
ordering, not an arbitrary sequence attribute. `ocel_stream` reuses that TraceSpec.
Selecting event_id would impose a lexical convention, not use native sequence.

The smallest next feature is therefore an **opt-in consumer profile**, tentatively
`observation-sequence-run/1`, onto the existing generic record-stream API. No new
engine algorithm is currently justified. Proposed contract:

1. Bind namespace to trusted source/export bytes and mapping version. A case key
   encodes the exact `(journal source_id, PiSession, run_id)` domain plus trusted
   installation/host scope. Never use agent ID alone or merge separate runs.
2. Preserve source event ID, original timestamp and exact source sequence. Check
   the selected run relationships and manifest identity before projection.
   Validate sequence as a nonnegative integer (not bool, nonfinite or fractional),
   unique in the case, with source-declared start and contiguous coverage for this
   complete per-run profile. Unknown domains, gaps and conflicting duplicates fail
   this profile; they do not cause renumbering or timestamp repair.
3. Set `RecordStreamSpec(order_policy="sequence", duplicate_policy="reject",
   close_cases=False, start_sequences=((case_id, 1),))` for these full journals,
   then use the existing sequence StreamingSpec. Keep `run_finished` an original
   activity and completion a source-sidecar fact; do not invent a terminal event.
   Original observations stay unchanged, and no time-based service measure follows
   from sequence adjacency. Clock regressions, if present, remain visible.
4. Preserve a separate projection/result identity, original OCEL hash and E2O
   mapping sidecar. This result describes observation adjacency for one case,
   not object-centric causal order, an OCDFG replacement, or resolved strict
   variants. Default OCEL `tie_policy="reject"` and the 68 results above remain
   unchanged. Partial/non-atomic, UNKNOWN and project-artifact limits propagate.
5. Before adoption, test unique tied-time source sequence, shuffled delivery with
   stable sequence, missing/fractional/duplicate positions, conflicting source
   IDs, same-agent different-run isolation, and native baseline/repair separation.
   No cross-case total sequence, handover or efficiency may be inferred.

This section is source inspection and an optional consumer contract proposal
only. No alternative projection was created or computed, no input was changed,
and no extra workload was run. Availability of the generic API is distinct from
consumer integration acceptance. A direct generic sequence option on OCEL object
operators would require a separately reviewed contract if later needed.

## Identity and coverage retained

OCEL Agent/Task/Run/Session attributes were matched directly to the native
manifest. Native runtime `task_id` equals job ID, not OrgTask. PiSession differs
from native OrgSession. The complete source-sidecar identities are retained in
the [run record](evidence/repository-persona-20261108/native/run-record.json).
Persona selection labels `profile-a`/`profile-b` are distinct from the OCEL
journal's `source_id`; neither is silently substituted for the other.

Failed SDK A and repaired SDK B have different native organization, job, OrgTask,
attempt, session and run IDs. The failed terminal event and manifest remain
`failed / PROGRAM_EXIT_FAILED`. SDK B is a separate deliberate goal, not an
in-run recovery or a new attempt inferred on the failed organization's task.
Context-input inclusion event counts match the handed-off values (2, 2, 2, 4).
No descriptor/body was read to reprove Persona binding or semantic influence.

Each native manifest retains verification `UNKNOWN`, and empty artifact_refs,
current_artifact_refs, evidence_refs and verification_results. All retain
`HOST_PROJECT_ARTIFACTS_NOT_CAPTURED` and the other host/program/cost limits.
The producer OCEL export `complete=true` is a per-run source flag; it neither
captures host-project files nor proves independent task acceptance. The
separately observed live project file was not opened or used as a native artifact.
Reported SDK usage remains simulated fixture data, not external billing.

Coverage remains partial for the combined case, with no atomic cross-run cut.
Source bundle digests and input/payload digests are preserved but not recomputed
from excluded raw content. Producer canonical OCEL digests were independently
recomputed from the approved documents and matched all four metadata sidecars.
PIX canonical source digests remain separately named. Handover is unavailable
without a reviewed message/organization projection; conformance is not attempted
without an independent reference model. No global/company OCEL, source sequence,
efficiency, artifact correctness or desktop acceptance follows.

## Reproduction and limits

From the PIX owner checkout:

```powershell
uv run --no-project --with tzdata python docs/reports/evidence/repository-persona-20261108/analyze.py D:/ChantaResearchGroup/pida-repository-profile-20261108 <fresh-output-directory>
```

The exact executed command, artifact hashes and imported producer verification
are bound in the [evidence manifest](evidence/repository-persona-20261108/source-manifest.json).
The [execution log](evidence/repository-persona-20261108/execution.txt) was converted
from PowerShell Tee-Object UTF-16 to UTF-8 without changing its text. This was
direct developer compatibility work, not a new independent review or producer
test-suite run. No additional engine regression test is warranted by the observed
native tie behavior.

Validity is limited to these exact approved bytes and engine revision. Withdraw
the result if source hashes differ, original identity/time/order is lost,
failed and repaired sources are collapsed, unknown coverage is erased, or a
computed process result is used to claim captured project artifacts or acceptance.
Organizational improvement remains unknown. The no-change alternative is retained:
the engine stays unchanged and the tied results remain unavailable.

Conclusion: the existing PIX engine supports bounded per-run descriptive analysis
of these approved repository/Persona traces, including explicit unavailable
strict-order results for the failed baseline; broader combined-product acceptance
is outside this evidence.
