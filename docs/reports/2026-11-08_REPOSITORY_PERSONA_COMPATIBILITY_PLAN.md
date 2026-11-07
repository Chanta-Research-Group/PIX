# Repository mode + Persona metadata compatibility: pending handoff

Scope: read-only compatibility of approved completed repository-mode program/project
runs with existing PIX `6e9af5ee1b670de39a87be406518fea49dffdfec`. No engine,
consumer, account, workload, model call or GUI changes. Working baseline is
`c0cfe3919cf51cbd5035cc9f7a1b91603a65b73b`, initially clean.

The pida owner has been asked for explicitly approved metadata-safe OCEL and
manifests, exact source/package hashes and native component identity. Until that
handoff, no private store, raw bundle, Persona context, goal or tool body will be
read. Packaged `e9a1d311` and external `f6` are task references, not yet independently
verified source hashes in this slice. Stock-host and scripted SDK proofs must
remain separately labelled.

Validation after the handoff:

1. Verify supplied approved paths and hashes, schema/exporter identity and scope.
   Bind each component to source, native run/PiSession, job, OrgTask and attempt
   through approved metadata. Missing lineage remains unavailable; do not infer it.
2. Confirm local engine source equivalence with the requested PIX revision before
   computation. Use only the approved native OCEL documents as computation input.
3. Recompute bounded per-run typed traces/DFGs, OCDFG, Run execution components
   and variants with native tie handling. Retain native statuses/issues and
   parent closure, and roundtrip serialized result artifacts.
4. Preserve every source event ID, original time and source-local sequence. Keep
   failed baseline and separate repair runs as different sources. Do not add a
   cross-run order, merge a global/company OCEL or infer organization efficiency.
5. Retain component availability, partial/non-atomic capture, native UNKNOWN,
   bundle/export/manifest limits and `HOST_PROJECT_ARTIFACTS_NOT_CAPTURED`.
   Computed process results must not imply project artifact capture or correctness.
6. Record source hashes, exact command/interpreter, native outputs and supported
   counts per run. Separate actual source facts, owner-reported provenance and
   direct computation. No timing/efficiency or whole-product claim follows.

Withdraw compatibility claims if input hashes/scope differ, identity is lost or
conflicting, failed/repair evidence is collapsed, unsupported ordering is invented,
or any coverage limit disappears. Validity applies only to the handed-off exact
exports and cited engine source. Organizational improvement remains unknown.

Initial status was pending approved exports. The exact approved handoff and
subsequent bounded direct results are now recorded in
[the compatibility report](2026-11-08_REPOSITORY_PERSONA_COMPATIBILITY.md).
The original plan remains as the intake record.
