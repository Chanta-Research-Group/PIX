# Actual single-task Pida trace investigation — 2026-11-07

## Evidence and execution boundary

This work reads one completed configured-model call using a synthetic task and
public Persona fixture. It makes no new model, credential, runtime or network
calls. It is not a two-organization trace or an improvement experiment.

The copied [observation bundle](evidence/live-pida-smoke-20261107/source/observation-bundle.json)
has byte SHA-256 `870f07cb277608845d52bf682db4bccf6e615959fb47632d3bbbdb8a065c824b`.
The original [start](evidence/live-pida-smoke-20261107/source/start.json) and
[result](evidence/live-pida-smoke-20261107/source/result.json) identify one actual
configured-provider request with one logical input inclusion receipt and a
matching marker response. They record unknown billed cost. No existing user
session was reopened for this analysis.

Historical consumer review revision is
`039d8ef3f153e1d8499566223fad876c8f2105b8`, Persona producer
`c1e3617aa88e6013ea34f76c3f4c41504618f863`. The
[source comparison](evidence/live-pida-smoke-20261107/historical-source-check.json)
matches all four recorded runtime/provider source hashes to that consumer Git
object. The one-shot harness was not present in that commit; its current file
matches the separately recorded hash and is retained as historical execution
evidence, never executed here.

The **later conversion** used actual Pida `exportOcel` from `dist/ocel.js`, not a
hand-built mapper. Its observed checkout HEAD was
`e98c23e4a1794e144ffaf700aa0b908b90515c7d`; imported module bytes were hashed
before/after execution. Node was v24.18.0. Its `src/ocel.ts` and `src/observation.ts`
have no Git diff from the corrected Windows revision
`c8a19f7002bb61a2836e039500091dc6e26694fb`. This does not imply the live call ran
on that later revision. [Exporter record](evidence/live-pida-smoke-20261107/export-record.json)
records actual compiled files and dependency-lock hashes.

PIX imported from this owner checkout at
`158e791dd601cf63ca02d3ebc824774dcfd86d3e`, Python 3.13.14. Git comparisons verified
that `src/pix` and `pyproject.toml` exactly match engine source pin
`3205d832d5dcdc6901f916b35496a0c60b657e7a` and have no local modifications.
This direct public-API probe does not replace any consumer commit allowlist.
Source identity/commands and artifact hashes are in the
[investigation manifest](evidence/live-pida-smoke-20261107/investigation-manifest.json).

## Observed input and supported results

Actual exported mapping is `pida.ocel20/1`; its
[OCEL document](evidence/live-pida-smoke-20261107/actual.ocel.json) imports as
`valid` with **no import issues or transformations**. PIX canonical OCEL digest
is `9d2aac265003068ff0a8985cad6f642780f297d9e48935a04e7ca3ec4400b637`.
This differs deliberately from the producer's canonical JSON digest and the
source file byte hash; those identities are recorded separately.

There are **9 events, 6 objects, 44 E2O relations and 6 O2O relations**. The object
types are Agent, Session, Task, Run, Turn and ModelRequest, one of each. There
are no Organization, Message, ArtifactVersion or Verification objects.

The per-run observation sequence is contiguous 1–9. All nine recorded timestamps
are distinct and increase in that order. The probe checks every source event ID,
sequence value and timestamp against the imported OCEL; no time is rewritten.
The observed word is:

```text
run_started → context_snapshot_loaded → run_context_loaded → turn_started
→ model_request → context_input_included → model_response → turn_finished
→ run_finished
```

`sequence_number` orders observations in this `(source_id, session_id, run_id)`
journal. It is not a cross-run or cross-agent causal order. In particular,
`model_request` preceding the logical input receipt in the journal does not
establish when provider bytes were sent or bypass the authorization evidence.

| Public computation | Actual result | Meaning |
| --- | --- | --- |
| Traces/DFG, each Agent, Session, Task, Run | computed; one object and 8 edges per layer | Every edge occurrence is 1; repeated layers are not additional source events. |
| Turn DFG | computed; one object, 4 edges | Five observed turn-related events. |
| ModelRequest DFG | computed; one object, 2 edges | Request, input-included and response observations. |
| OCDFG over all six types, reject ties | computed | Six separate typed layers; O2O retained in OCEL but does not invent DFG edges. |
| Execution extraction, Run/run E2O only | computed; one execution covering nine events | Explicit run scope, not organization discovery via shared agent. |
| Exact variants for that execution | computed; one variant, frequency 1 | Shape summary of one selected run, not a learned organization standard. |
| Temporal Run gaps, 1ms precision | computed | Eight intervals between observations; service time unavailable without a start attribute. |
| Message handover attempt | native invalid_input, `unknown_object_type` | No Message carrier type exists; this is not a zero-delay or zero-handover claim. |
| DFG/Petri-net/OCPN alignment | not run: no independent selected reference model | No fitted-to-self conformance score or live object-cut verdict invented. |

The Run point timestamp span is 4.158 seconds, from `12:10:22.296Z` to
`12:10:26.454Z`. It is one observed span, not service time or a performance
estimate. At 1ms precision the logical input receipt → model response gap is
4,047,000–4,049,000 microseconds; the context snapshot → run-context gap is
0–2,000 microseconds. No fabricated finer precision is used.

The [final native record](evidence/live-pida-smoke-20261107/native-final/run-record.json)
contains 18 native result documents with closed parent-artifact references and
byte roundtrip checks. Its source hashes bind the original bundle, actual export
and investigation script. The earlier `native/` directory is an incomplete probe
that missed the temporal result's precision-specific trace parent; it is not a
passing artifact bundle. The final probe includes that parent and verifies
parent closure before publication. This was investigation harness bookkeeping,
not a PIX engine defect.

## Scope and lineage limits

The bundle/export `complete=true` means source capture completion. The manifest
still declares `verification_status=UNKNOWN`, no artifact/evidence refs and
`NO_INDEPENDENT_TASK_ACCEPTANCE`, `FINAL_ARTIFACT_STATE_UNCONFIRMED`,
`PI_INTERNAL_REQUEST_USAGE_NOT_EXPORTED` and `COST_UNKNOWN` among its limits.
The exporter has its own smaller limit list; consumers must retain both sidecars
instead of turning OCEL completeness into task acceptance.

The original Persona descriptor contains synthetic `host:one`, `session:fixture`,
`instance:main`, `attempt:one`. These remain historical facts about the harness;
they are not native organization/attempt identities. The descriptor is excluded
from native OCEL by the producer, so these bindings cannot be recovered from the
six object types alone. Source hashes bind the retained original evidence, not
a newly inferred host or organization.

Pida owner confirms the current host correction uses actual `job.attemptId`,
while the external task reference is `job.id`; native organization task identity
is separately available as `job.organizationTaskId`. The later adapter's
send-intent/dispatch/receipt records are separate sources, not events retrofitted
into this old single-run bundle.

## Next smallest consumer binding

Bind one actual authorized job export to the adapter receipt by exact job ID,
then preserve its genuine native attempt, organization task, run, session and
agent IDs alongside host/organization-session/binding revision. Keep the
authenticated owner + producer/request/recipient carrier scope and all source
hashes. Map current binding fields into qualified objects or a validated immutable
sidecar; the reviewed PIX fixture already proves that changing them must change
applicability/source identity. Do not label native Pi session as organization
session or infer attempt ID from run ID.

The next acceptance check should compare those actual producer and consumer
bytes through Schumpeter's real projection. For this source, timestamp ties do
not block supported descriptive computation. Unknown organization binding,
missing message/artifact evidence and absent independent reference models bound
the remaining questions. Preserve pending/unknown rather than synthesizing events,
microtimestamps or a desired model. The do-nothing alternative is to continue
descriptive Run-level analysis while those bindings are supplied.

No new regression test or engine change was justified: no supported engine defect
was reproduced. Developer probe assertions and native roundtrips ran; independent
review of this actual-data investigation and desktop acceptance did not.
The preceding [independent fixture review](2026-11-07_PIX_MAPPING_REVIEW_RECEIPT.md)
remains a separate scope.

Falsify these results if source/export hashes do not match, source IDs/times/order
change during projection, required manifest limits are lost, or actual binding
cannot join the authorized receipt to its native job. Refresh after producer,
mapping, engine or scope changes. Organizational efficiency improvement is
**알 수 없음** from this single trace.

Conclusion: **PASS for supported descriptive PIX computation on this historical
single real-model trace**; two-organization, task acceptance and desktop
integration claims remain unsupported by this evidence.
