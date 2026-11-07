# Exact native sequence composition: bounded limitation

Input is only the approved saved `sdk-profile-a` metadata already verified at
PIX evidence commit `e36d7864f64c1a979ef612a31084eb62c89d3702`. Its source run
`04fc92fd-2842-4920-9548-5ae6a627df93` remains failed / PROGRAM_EXIT_FAILED,
with UNKNOWN verification and HOST_PROJECT_ARTIFACTS_NOT_CAPTURED. No private
state, model call, workload, OCEL edit or engine change occurred.

Existing PIX engine `6e9af5ee1b670de39a87be406518fea49dffdfec` was used with
`RecordStreamSpec(order_policy="sequence", start_sequences=((case_id, 1),),
duplicate_policy="reject", close_cases=False)` and sequence StreamingSpec.
The case domain binds original journal source_id, PiSession and run; its namespace
binds this mapping version and approved OCEL byte hash.

The record projection computes all 16 original events with native positions
1–16. Original source event IDs remain in occurrence provenance; generated
projection IDs are separately identified. Timestamps, activities and native
sequence match exactly. Seven isolated synthetic negative mapping probes reject
absent, duplicate, fractional and boolean sequence, mixed source domain, duplicate
source event ID, and a missing position. Declared full-run start/end and native
Agent/Task/Run/Session relationships are validated before projection.

Delivery through existing CaseStream is **unavailable**: operation zero reports
`out_of_order: a new case must start at sequence zero`. No DFG is produced, and no
native position was silently subtracted, no start event invented, and no gap
renumbered. Both native result artifacts roundtrip; delivery references its exact
projection parent. Before/after hashes prove all 82 files in the earlier native
evidence tree unchanged, including its 68 strict results and 10 unavailable ones.

Reproduce with a fresh output directory:

```powershell
uv run --no-project --with tzdata python docs/reports/evidence/observation-sequence-20261108/analyze.py <fresh-output-directory>
```

[Result/provenance](evidence/observation-sequence-20261108/native/run-record.json)
and [manifest](evidence/observation-sequence-20261108/source-manifest.json) bind the
exact script, configuration, inputs, output hashes and Python version. The log was
converted from PowerShell UTF-16 to UTF-8 preserving text and CRLF.

This is a derived single-run observation/case projection, not replacement of
strict native OCEL/OCPM outputs or evidence of causal order, artifact correctness,
atomic organization coverage or efficiency. The no-change option retains the
unavailable delivery. A separately authorized transport-offset contract may
address the adapter boundary while retaining original native sequence in an
invertible provenance mapping; it is not applied to these artifacts.

Validity is limited to the cited source/API and input bytes. Withdraw this
limitation if the same unchanged API accepts native sequence 1 as a new case or
the repro fails to preserve source positions. Conclusion: exact native-sequence
record projection is supported, while unchanged CaseStream delivery of this
1-based sequence is unavailable.
