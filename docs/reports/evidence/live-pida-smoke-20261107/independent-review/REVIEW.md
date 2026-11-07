# Independent review of historical Pida trace analysis

Reviewer: `/root/pix_mapping_review`, separate context, same Codex family.
Reviewed PIX commit: `afc3f4719b9406fb5fe1d7750af30fbedee72f1a`.
Detached checkout: `D:/ChantaResearchGroup/PIX-live-review-20261107`.
No implementation files, live runtimes, credentials or user sessions were changed.
No model call or network/provider execution was made by this review.

## Independently reproduced evidence

Command executed against the frozen checkout:

```text
uv run --no-project --with tzdata python docs/reports/evidence/live-pida-smoke-20261107/analyze.py --output D:/ChantaResearchGroup/PIX-live-review-evidence-20261107/native
exit_code: 0
tool chunk: 14a2bc
```

The analyzer uses unmodified PIX public APIs and read-only Git comparisons. The
separate reviewer script `verify_artifacts.py` checks source files, Git blobs,
native artifacts and event projection independently of its assertions. Results
are in `artifact-verification.json` (tool chunk `4f54cc`).

- All 11 investigation-manifest source hashes and 7 native-record source hashes
  match. Bundle byte SHA-256 remains
  `870f07cb277608845d52bf682db4bccf6e615959fb47632d3bbbdb8a065c824b`.
- Four recorded runtime/provider source hashes match the actual Git blobs at
  historical consumer `039d8ef3f153e1d8499566223fad876c8f2105b8`. The harness
  is correctly treated as a separately hashed file, absent from that commit.
- Five later exporter source/package/lock hashes match Git blobs at
  `e98c23e4a1794e144ffaf700aa0b908b90515c7d`; `ocel.ts` and `observation.ts`
  match their corrected Windows revision `c8a19f7002bb61a2836e039500091dc6e26694fb`.
  This review did not rebuild or rerun the later compiled JavaScript exporter.
  Its recorded module hashes remain historical execution evidence, distinct
  from independently checked Git source bytes and the live-call source.
- Exported document equals the retained `actual.ocel.json` data. Both producer
  canonical JSON digests recompute correctly. PIX's different canonical OCEL
  digest is `9d2aac265003068ff0a8985cad6f642780f297d9e48935a04e7ca3ec4400b637`.
- Import is valid with zero issues and transformations: 9 events, 6 objects,
  44 E2O and 6 O2O relations. Every original event's activity, source ID, event
  ID mapping, timestamp and sequence value matches. Sequence is exactly 1–9,
  with distinct increasing times in one source/session/run journal. The
  observed point-timestamp span is 4.158 seconds, not a service-time estimate.
- All 18 regenerated native result documents match the frozen bytes, hashes,
  computation IDs and native codec roundtrips. Every parent computation resolves
  to the recorded artifact. The regenerated run record differs only in
  `imported_checkout_head`, which correctly becomes the reviewed documentation
  commit instead of the owner's earlier engine checkout.
- Agent/Session/Task/Run DFGs each have 8 edges; Turn has 4; ModelRequest has 2.
  These layers reuse the same observations and are not additional runs. One
  selected Run execution and one variant are descriptive results only.
- The handover result is `invalid_input` / `unknown_object_type`, as the six
  types are Agent, Session, Task, Run, Turn and ModelRequest. It is not a zero
  handover result. No alignment/reference-model analysis was run.
- `host:one`, `session:fixture`, `instance:main`, and `attempt:one` are absent
  from exported OCEL. The original descriptor stays retained as synthetic
  harness evidence and is not promoted to native organization/attempt identity.
- Source-completeness and task acceptance remain separate. Both exporter and
  bundle-manifest limits are retained; task verification remains UNKNOWN,
  artifact state unconfirmed, detailed request usage unexported and cost unknown.
  No organizational efficiency or semantic-benefit claim is supported.

The engine/package diff against pin `3205d832d5dcdc6901f916b35496a0c60b657e7a`
is empty. No additional regression suite was justified for this read-only
investigation; this is an actual rerun of the analyzer and independent artifact
checks, not a rebranding of historical tests.

## Recommended Schumpeter binding record

This is a proposed consumer-side applicability record, not an implemented API or
proof that this old bundle can supply absent fields. Preserve raw producer IDs
and raw artifacts; record native projected IDs additionally rather than replacing
the source IDs. Use a versioned immutable sidecar (or equivalent qualified OCEL
objects) whose canonical digest participates in projection/cache applicability.

| Group | Required evidence and validation |
| --- | --- |
| Authenticated delivery | Trusted owner scope; producer/request/recipient-organization carrier tuple; exact envelope digest; receipt ID and byte hash; receipt's exact `job_id`; phase and durability scope. The sender body does not authenticate owner scope. |
| Native execution | Authoritative host ID, native organization-session ID, agent ID, job ID, `job.attemptId`, `job.organizationTaskId`, Pi session ID and run ID. Link by the receipt's exact job, then checked producer metadata. Preserve persistent Schumpeter organization ID separately. |
| Observation identity | Bundle byte hash and producer canonical source digest; `(source_id, session_id, run_id)` sequence scope; event IDs/positions/times; bundle manifest and exporter coverage limits. Exported `task_id` is the runtime task reference, not automatically native organization-task ID. |
| Persona | Negotiated protocol/capabilities; binding ID/revision/digest; context/input receipt references and actual supported evidence phase. Synthetic historical descriptor IDs must stay marked unavailable for native joins. |
| Transformation | Historical runtime source manifest and harness hash; later exporter source/module/mapping identity; OCEL byte/producer/PIX digests; PIX engine identity, operator/spec and all parent result artifacts. Different lineage must invalidate cached applicability even if numerical results coincide. |

At inspected Pida `e98c23e`, the supervisor calls the runtime with
`{taskId: job.id}` and separately keeps `job.organizationTaskId` and
`job.attemptId`. The native Pi session is not the organization session. Do not
derive attempt from run ID or organization from Persona descriptor text.

For this historical single-run bundle there is no authenticated collaboration
receipt or native organization/attempt mapping to complete the proposed record.
Keep those fields unavailable and limit the display to descriptive Run analysis.
The next check should bind a new actual authorized job export to its exact
receipt and metadata, then run Schumpeter's real projection; no old event or
timestamp should be retrofitted to make that scenario appear present.

## Review scope

The evidence proves reproducible supported descriptive computation over the
retained historical trace. It does not independently observe the original
provider wire exchange, validate full historical dependency/build closure,
authenticate the historical user, or establish task correctness, cross-org
handover, live Persona continuity, desktop acceptance or improved efficiency.
Those limits are consistent with the investigated report. No material finding
requires a code correction in this bounded investigation.

Validity is restricted to the reviewed commits, artifacts, mapping and selected
operator specifications. Reopen review if source hashes disagree, projection
changes identity/time/sequence, parent artifacts fail closure, coverage limits
disappear, or an inferred native binding is substituted for producer evidence.

Verdict: **PASS for this historical single-run descriptive analysis and its
artifact record**, with production Schumpeter binding and desktop acceptance
remaining open.
