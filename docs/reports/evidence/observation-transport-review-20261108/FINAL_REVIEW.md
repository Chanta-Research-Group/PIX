# Independent observation transport projection review

Reviewed 2026-11-08 in detached `D:/ChantaResearchGroup/PIX-transport-review-20261108` at `cba1dc185846338eeeb839645a7a1a1071924692`. This report covers one approved, saved, failed SDK run. Review artifacts are external to the author repository. No application, workload, model, package build, engine modification, or private database/raw context access was performed.

## Evidence and reproduction

The reviewer executed these commands from the detached worktree, all exit 0:

```text
uv run --no-project --with tzdata python docs/reports/evidence/observation-transport-20261108/project.py D:/ChantaResearchGroup/PIX-transport-review-evidence-20261108/reproduced
uv run --no-project --with tzdata python docs/reports/evidence/observation-sequence-20261108/analyze.py D:/ChantaResearchGroup/PIX-transport-review-evidence-20261108/exact-reproduced
uv run --no-project --with tzdata python D:/ChantaResearchGroup/PIX-transport-review-evidence-20261108/audit.py
```

Python was 3.13.14. `audit.py` independently compared approved upstream Git blobs, event mappings, native serialization, source/config identity and rejection behavior; it did not merely accept the author's check booleans. `audit.json` contains checked paths/hashes and individual probe outcomes. `artifact-index.json` indexes this review's files.

The four approved upstream blobs (handoff, SDK-A OCEL, manifest and meta) are byte-identical to the pinned producer `ff68457f7d032bfa0aa81badf27bdf4079cadc5e` under its approved `metadata-only` directory. This establishes the metadata handoff link; it does not independently re-export raw runtime data or verify model input bodies.

All 99 files under the three relevant evidence directories matched their respective frozen Git blobs: strict evidence `e36d7864f64c1a979ef612a31084eb62c89d3702`, exact-sequence evidence `cb0917ca3c1b14582474a436b9a69d596816083c`, and transport evidence `cba1dc185846338eeeb839645a7a1a1071924692`. The 92 prior files remain unchanged. All 68 strict native result files round-trip without byte changes: 58 computed and 10 unavailable. These results were checked for preservation/serialization, not independently recomputed in this slice.

Both new native results and the complete run-record reproduced byte-for-byte. Native result SHA-256:

| Artifact | Status | SHA-256 |
| --- | --- | --- |
| record-projection.json | computed | `9f2cd4b6a5c8480e943073033584fb6939d48d73fc01534a82e323fd51f23723` |
| sequence-delivery.json | partial | `3e4013bc005e44f7973e8915319646c47e4faf92f195cf4c353accfed4ae6324` |

The delivery references the projection computation as its exact sole parent. The separate original 1-based composition again produced a computed projection followed by unavailable delivery, with `a new case must start at sequence zero`; its two native results also matched the preserved originals exactly.

## Mapping and API observations

At `project.py:40`, the transport validates integer/non-boolean sequence, one source domain, exact declared contiguous cut and unique source event IDs before applying the reversible offset. At `project.py:70`, its pinned upstream validator checks the native Run, Session, Task and Agent objects and qualified event relationships, then derives the case domain from the validated source and handoff identity. See `observation-sequence-20261108/analyze.py:35`.

Independent comparisons established that all 16 original OCEL IDs, source event IDs, timestamp strings, payload digests, relationships and native sequences survive in the mapping. Native sequence 1..16 becomes transport 0..15, with inverse +1 for every event. The tied timestamps at native positions 2 and 3 remain `2026-11-07T18:34:21.847Z`. Reversing input delivery reproduces the same validated mapping. The single-run domain is original journal source ID plus PiSession `01a1b74a-4af4-7022-aefa-91928bb1f6be` and run `04fc92fd-2842-4920-9548-5ae6a627df93`; job `91f29a2e-547d-4db9-ba9e-f9b329e252a1` remains bound through its native Task object.

The reviewer independently rejected eight mapping corruptions and five additional domain corruptions: absent/duplicate/fractional/boolean sequence, different source, duplicate source event ID, missing event, wrong declared start, wrong manifest run/session, wrong native Run/Session identity, and removed event-to-Run relation. These were synthetic in-memory copies of approved metadata, not altered source files.

At `project.py:74`, the namespace binds mapping profile, domain, declared cut, formula/inverse and original handoff/OCEL hashes. Existing `stream_adapters.py:383` fingerprints every input column. Three retained-provenance mutations (native sequence, payload digest, OCEL event ID) changed source and computation identity; three policy mutations (handoff hash, profile, cut) changed computation identity. These identity probes deliberately bypass mapping validation and do not imply corrupt input would pass the complete entrypoint.

`src/pix` and `pyproject.toml` match engine pin `6e9af5ee1b670de39a87be406518fea49dffdfec`. The existing zero-based fresh-case rule at `streaming.py:881` remains unchanged. The new result follows existing API behavior, not an engine compatibility modification.

The independent adjacent-activity count agrees with the delivery: 12 distinct edges and 15 occurrences from 16 observations. No synthetic start/end marker or close operation exists. The source's `run_finished` and `failed / PROGRAM_EXIT_FAILED` remain facts; the monitor retains one open case, zero closed cases and `open_cases`, so delivery is partial. Verification remains UNKNOWN and the organization snapshot remains non-atomic. Equal timestamps were not repaired.

## Limits and withdrawal criteria

This is a pinned evidence script, not a general externally callable ingestion/security boundary. `transport()` alone does not authenticate a run/session supplied by an arbitrary caller; the reviewed `run()` entrypoint derives those fields after pinned metadata and native-domain validation. Any future consumer must preserve that composition and review its own authority boundary. No Schumpeter adoption is authorized by this review.

No native OCEL/OCPM replacement, cross-run causality, organization aggregation, model quality, project-artifact completeness, conformance or efficiency improvement is established. The reviewed SDK source uses the previously disclosed scripted responses; this is not evidence of a new live model execution. The previous strict timestamp-related unavailable results remain unavailable.

This assessment is valid only for the exact source, input, engine and artifact hashes indexed here. Withdraw it on changed source/domain/cut/provenance, a lost or altered original field, acceptance of a malformed cut, identity collision under changed retained provenance/configuration, changed prior outputs, synthetic closure or failure-state erasure, or promotion into a different consumer/authority scope without separate review. Behavior outside these inputs is unknown.

Conclusion: no material defect found in the frozen, approved single-run observation transport projection; the bounded evidence supports its explicit invertible mapping and partial native delivery, with all stated limits retained.
