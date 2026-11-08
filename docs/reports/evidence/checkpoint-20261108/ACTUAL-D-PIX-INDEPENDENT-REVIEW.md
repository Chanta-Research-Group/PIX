# Independent actual D same-trace PIX audit

Reviewed 2026-11-08 KST for fresh case `5bd55085-d316-4dc3-97cf-091d70a32478`. This is a read-only audit of the actual separately approved A/B linked UI outputs. No model call, service/app launch, GUI action, engine edit or source-workspace mutation was performed by this reviewer. Offline PIX recomputation writes only this independent evidence directory.

## Exact source and package

- Schumpeter product: `7cf0a07750e5b60ab127ad1fa1813b3542446daa`.
- Pida runtime: `b7f7d523c6fede56d508575a6bb78afa343e5566`.
- Candidate D path-r1 Windows inventory SHA-256: `0812aae58b612dabe24bb353da5f86e13ce069c0506283a99e5060b6498d412d` (17,171-file inventory). The reviewer checked this inventory's identity and 282 selected Schumpeter/PIX source, runtime/manifest and ASAR files against it; this is not a new full-package tree scan.
- ASAR: `54986497133c0930c8eec552b13567a0623cbae11aff283c468903bdcabdff53`.
- Service manifest: `5d8e4bd62f23bb7a4fa1db3f912818707253211966755bc46c269c3690322c98`.
- Pida manifest: `36388ea34cbe9011c1554b389cbdc55dd7789914f862ab744b6587b6e4fcf88f`.
- Packaged Python executable: `d718435b892db4ad5b547d12fec61be7baa7faf7a58d857ea58053be24c7a000`. PIX reports version 0.5.0 and source-tree SHA-256 `15d52fb08225a47f5732e02c69ab7edebd61e068b431da4d0aa8aeb201fb2cee`; Git commit is explicitly null/unverified. Official-Python bridge reports `frozen=false`, with actual package source/runtime hashes, rather than pretending to be a frozen-bytecode or clean-Git attestation.

The linked/root analysis implementations remain the previously reviewed source. Actual captured producer inventories match both their designated runtime cache and packaged D producer files. No fixture runtime, trace substitution or synthetic scope relabelling was used for these analyses.

## Actual selected analyses and native lineage

| Organization | Reservation | Analysis ID | Captured/expected |
|---|---|---|---|
| A | `be2defe1-0c18-425a-b3a0-89e968519584` | `e2819c8f63fb6c2b1f4c933a846ef5678f8d48710b965de8d56e310a2ec5bd1c` | 3/3 |
| B | `72766938-54f5-448f-bec6-4537e549275d` | `438508c3208d4635b058f24f9f2507a99b3c675c0e009864d95ea236f819a0bf` | 1/1 |

A and B have distinct explicit linked grant IDs, each captured at revision 1 and `local-private`, bound to the exact source, host, reservation and binding revision. The profile grants no execution authority. The recorded provider mode is `configured-native-chatgpt`; this audit does not infer provider identity merely from a label, and independently checked the four run identities against the separately supplied safe actual-case observations.

| Actual job | Role | Events / objects | Native result files |
|---|---|---:|---:|
| `6080e981-de8a-4d5e-a14b-571088764a70` | A initial root, yielded | 23 / 12 | 17 |
| `6745cb3d-3859-4e6f-bfd7-6b99a89903a4` | A child | 9 / 6 | 15 |
| `05863fc6-c183-42e4-aaab-e9fe4352cbbb` | A continuation, attempt 2 | 17 / 11 | 21 |
| `d50e906c-141f-4a57-a6cf-c7f8ea37c54f` | B fresh organization root | 17 / 11 | 21 |

These are separate per-run counts. They are not summed unique organization/company events or objects. All listed native result files have computed status; manifest task verification remains UNKNOWN for every run.

A's native organization is `29569444-4941-4096-8cfc-8d79cbd88814`; B's is separately `92330d94-e275-40ab-a216-56d39bd1d946`. Original receipt/task/attempt IDs match their initial jobs. A join `ea8cda06-e155-4b99-9de8-7d2754f545bb` binds root6080 → assignment child6745 → continuation0586 with exact revision and task/attempt links. The continuation is not rewritten as the admission root. Child and root agent IDs remain distinct; continuation shares the actual root task/Pi session where the producer does. Native Pi session/run are not replaced with OrgSession/OrgTask IDs. B is not inferred from a same-agent lookup or an A continuation.

The A continuation and B component manifests retain exact observed artifact ID/path/SHA/byte metadata matching the safe case observations. No artifact contents were opened by this reviewer. Native artifact/version metadata is not conflated with Schumpeter publication or acceptance revision; that workflow is reviewed separately.

## Independent data and computation checks

The audit reads only the two exact approved linked analysis directories and the designated safe UI/case files. It verifies source metadata digest and complete analysis-cache identity, separate grants and full original receipt/binding facts; ordered membership; exact job/agent/task/attempt/run/Pi-session joins; child parent and continuation join/revision; and the two stable before/after membership hashes. Equal reads remain `snapshot_atomic=false`, not a transactional guarantee.

Within each component, original source IDs, source event IDs, timestamps, observation sequence (1 through that run's final sequence), payload digests, manifest and native export are retained. Event metadata has no source payload. Membership/job/event/manifest fields obey the closed projection vocabulary; native event attributes exclude Persona descriptor. No prompt, model result, tool-argument body, raw seed or artifact bytes were inspected or copied. The recorded model-request occurrences are 3/1/2/2; this is observation accounting only, with no new call or billing/cost inference.

All **74 individual native result files** were independently recomputed from the saved approved OCEL using the packaged PIX modules and packaged Python (`-I -B`), without starting the service bootstrap. Results compare equal to the saved native objects, including exact computation IDs, source digest, status/issues and parent computation closure. Each selected UI Agent DFG JSON equals the file for that exact job and computation ID. The actual A/B screenshots were inspected read-only: they show the corresponding organization, continuation/B-root identity, per-run counts, UNKNOWN and native operator JSON. This is screenshot corroboration of the collected result, not a fresh interactive GUI test.

The offline interpreter naturally lacks the service bootstrap's published packaged-manifest descriptor. The reviewer compared all other engine identity fields directly and independently verified the recorded extra manifest hash from its actual bytes. It was not silently injected or presented as a fresh bootstrap execution.

Both indexes retain `coverage=partial`, `snapshot_atomic=false`, UNKNOWN and separate bundle/manifest/export limits despite 3/3 and 1/1 captured observed jobs. Neither report exposes a merged/global OCEL, global DFG, handover, conformance or efficiency score. Native task verification, computed PI, provider input inclusion, artifact acceptance and business correctness remain separate claims.

## Original export provenance boundary

Approved pida comparison receipt: `two-org-case-d-ocel-comparison-20261108.json`, SHA-256 `efcbcc3f1034bb8988042d8412d060e61d26bd2ca33cc1d00589fee851210bb2`.

For every run, the reviewer independently recomputed the captured canonical OCEL digest and the ordered projection of native event ID/type/time/source ID/source event ID/sequence/payload digest. They equal the receipt's original-document and original-event-projection digests. The receipt's original file hashes also match the earlier safe A/B observation records. Its exact captured component path/file hash matches the reviewed component, and the copied source metadata equals the row capture. Actual event/object attribute-name inventories match the receipt's inspected metadata-only vocabulary.

The producer owner performed the original-file inspection and approved this hash-only receipt. This reviewer **did not open raw private bundles, Pi journals, Persona/history, submitted goals or result bodies**. Original→captured provenance therefore combines the owner's original-file comparison with this independent captured-data/hash verification. `meta.sourceDigest` is a stored-meta binding, not an independently repeated raw-bundle export. No stronger access or re-export claim is made.

## Evidence, limits and withdrawal

`audit.py` is the executable offline check; `audit.json` records 96 exact input file hashes, package source hashes, engine identity, grant IDs, all four exact run/source identities, sequences/times, separate native counts/statuses and selected computation IDs. Approved metadata/UI copies and verified native files are retained beneath this directory. All input bytes were checked unchanged at the end of the audit. The original comparison receipt is copied alongside; original body-bearing evidence is not.

The final `evidence-manifest.json` binds this report, executable audit, completed audit record, approved original-comparison receipt, safe metadata/UI copies and verified native files. Its final audit record includes the completed original-comparison receipt check; earlier pending-stage tool summaries are not the final proof.

This audit accepts the exact **actual D same-trace linked PIX path**, not the complete desktop, Linux, workflow oracle, publication/acceptance, Persona causality, exact provider-wire payload or organization improvement. Other reviewers own those gates. No further execution is needed for this PI audit; the no-action alternative preserves the completed evidence. Costs and efficiency benefit remain unknown.

Validity is limited to the listed case, source/package identities and captured cuts. Withdraw the assessment if a run/job/source ID is replaced, original comparison digests cease matching, an unauthorized profile/body enters the projection, any native recomputation or parent closure fails, selected UI JSON belongs to another job, or partial per-run results are promoted to complete/global/efficiency claims.

**Verdict: the actual D A3+B1 linked metadata and per-run PIX results pass this independent same-trace audit, with the original-export provenance and broader-product limits above.**
