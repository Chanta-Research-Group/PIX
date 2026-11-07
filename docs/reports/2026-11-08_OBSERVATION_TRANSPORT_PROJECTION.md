# Explicit observation transport projection: one approved failed run

## Separate scope and preserved baseline

This is the separately authorized opt-in profile
`pix.owner.native-sequence-transport/1`, using only existing generic PIX
`records_stream` and `StreamingSpec(order_policy="sequence")` APIs. Engine
`6e9af5ee1b670de39a87be406518fea49dffdfec` is unchanged. No OCEL file, source
timestamp, workload, model, private state or default ordering policy was changed.

The prior strict compatibility evidence at `e36d7864f64c1a979ef612a31084eb62c89d3702`
keeps all 68 outputs, including 10 unavailable strict results. The faithful
1-based stream composition failure is separately preserved at
`cb0917ca3c1b14582474a436b9a69d596816083c` in
[its report](2026-11-08_EXACT_SEQUENCE_COMPOSITION.md): record projection computed,
but fresh CaseStream delivery rejected its first native sequence 1 because the
stream protocol requires zero. The current result does not overwrite that fact.

Input remains the approved saved SDK-A failed baseline from pida handoff
`ff68457f7d032bfa0aa81badf27bdf4079cadc5e`, copied and byte-verified during the
strict analysis. Its run is `04fc92fd-2842-4920-9548-5ae6a627df93`, job
`91f29a2e-547d-4db9-ba9e-f9b329e252a1`, PiSession
`01a1b74a-4af4-7022-aefa-91928bb1f6be`. The failed runtime state and distinct
repaired goal remain separate; no repaired-run data enters this projection.

## Mapping contract

The case domain contains the original OCEL journal source_id, exact PiSession
and exact run ID. Namespace identity binds the approved OCEL and handoff byte
hashes, domain, mapping version and declared cut. Persona selection labels are
not substituted for the journal source ID. Host/owner identity is not fabricated;
this is an already approved saved-metadata calculation, not an authentication API.

Before mapping, the producer manifest and native Agent/Task/Run/Session objects
must agree with the approved sidecar. Every event must relate to those objects
with the expected qualified E2O. Source event IDs must be unique and all events
must belong to one source domain. Sequence values must be integer, not bool or
fractional, unique and contiguous over the explicitly declared full cut 1–16.
The observed start and terminal activities remain run_started and run_finished.

The only new index is explicit and invertible:

```text
declared_first_native_sequence = 1
transport_sequence = native_sequence - declared_first_native_sequence
native_sequence = transport_sequence + declared_first_native_sequence
```

Native sequence, original event/OCEL IDs, activity, exact timestamp string,
payload digest and qualified relations remain in the persisted mapping. The
existing record-stream API fingerprints all mapped input columns, including
native_sequence and provenance. Its generated occurrence IDs separately preserve
the original event ID through StreamOccurrence.source_event_id. RecordSpec selects
`sequence_key="transport_sequence"`, start 0, duplicate reject, and close_cases
false. This does not alter the native sequence or fill gaps; the offset is fixed
by the declared cut and is not inferred from whichever events happened to arrive.

The transformation changes the adapter's transport index, not event order.
The two native events at `2026-11-07T18:34:21.847Z` keep that exact time and native
positions 2 and 3, while their transport positions are explicitly 1 and 2.
No global sequence, cross-run relation or timestamp repair is introduced.

## Direct result and checks

The record projection is computed. Sequence delivery is **partial**, with native
`open_cases`: 16 accepted original events, one case, zero closed cases. No synthetic
start/end event was inserted. The source run_finished activity and failed terminal
manifest remain intact; runtime termination is a source fact, while monitor
closure requires a separate explicit stream protocol operation that was not added.

The resulting observation-adjacency DFG has 12 distinct edges and 15 occurrences.
Activity counts and every edge count match adjacent original native-sequence
activities. This is a derived per-run observation/case DFG, not a replacement
OCDFG or resolution of the earlier strict timestamp-based object trace results.
It provides no causal, conformance, efficiency or project-artifact claim.

Eight isolated synthetic mapping probes reject missing, duplicate, fractional
and boolean sequence values, mixed source domain, duplicate source event ID,
a gap, and a wrong declared start. Reversing delivery order produces the same
validated mapping. An independent identity probe confirms that altering retained
native provenance changes the record-stream source/computation identity; this
probe bypasses the application validator solely to inspect hashing and is not an
accepted mapping. A changed run domain changes case/mapping identity.

Both native artifacts roundtrip exactly, and the delivery's parent resolves to
its captured projection artifact. Before/after SHA-256 verification preserved all
92 prior evidence files checked, including the strict native output tree and the
exact-sequence failure artifacts. The validator source is pinned to `cb0917c`.
No engine regression tests were added because engine code is unchanged; these
are bounded mapping/developer assertions, pending independent review.

UNKNOWN verification, partial/non-atomic coverage, PROGRAM_EXIT_FAILED,
HOST_PROJECT_ARTIFACTS_NOT_CAPTURED and all other original manifest/export limits
remain in the [result record](evidence/observation-transport-20261108/native/run-record.json).
Empty artifact/evidence lists remain empty. Producer model responses/usage are
scripted fixture data. No descriptor, context, goal, tool body or live file was
read for this result.

## Reproduction and withdrawal

```powershell
uv run --no-project --with tzdata python docs/reports/evidence/observation-transport-20261108/project.py <fresh-output-directory>
```

The [source manifest](evidence/observation-transport-20261108/source-manifest.json)
records the exact command, Python 3.13.14, mapping/configuration/result hashes,
and evidence paths. PowerShell's execution log was converted from UTF-16 to
UTF-8, preserving text and CRLF. These files are a local review unit, not a deployed
consumer profile or independent acceptance.

Keep the default strict profile unchanged. The no-change alternative remains
using its unavailable results and the recorded exact-sequence delivery failure.
Withdraw this mapping claim on a changed domain/cut/input hash, noninvertible
offset, any lost native position/identity/time, gap renumbering, hidden duplicate,
or erased failure/coverage state. Validity is only this exact approved run and
generic API revision. Organizational improvement is unknown.

Conclusion: the explicitly mapped zero-based transport index supports a partial
single-run observation DFG while preserving native 1-based sequence and all
source limitations; independent mapping review remains the next gate.
