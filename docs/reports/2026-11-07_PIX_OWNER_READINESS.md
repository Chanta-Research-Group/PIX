# PIX owner readiness and contract intake — 2026-11-07

This work slice checks whether the PIX owner can supply a bounded integration
oracle to the four-app effort. It does not accept a new consumer profile,
change an execution policy, or certify the four applications together.

## Source and workspace evidence

| Item | Observed value |
| --- | --- |
| Original checkout | `D:/ChantaResearchGroup/PIX`, branch `feat/ocel-readers-v0.2.0` |
| Original HEAD | `a0688f34e557c885c145051485072fd0623f263f` |
| Original origin | `https://github.com/riesling-29/PIX.git` |
| Original dirt | Only untracked `docs/PIX_review_5ef88a2.zip`; untouched |
| Refreshed GitHub main | `Chanta-Research-Group/PIX` at `6e9af5ee1b670de39a87be406518fea49dffdfec` |
| Main tree | `1c19a781712d7d7b57d53c7f602428b9bb4edf48` |
| Open PR intake | GitHub open-PR query returned an empty list on 2026-11-07 |
| Owner checkout | `D:/ChantaResearchGroup/PIX-owner-20261107` |
| Owner branch and HEAD | `work/pix-owner-intake-20261107`, same main SHA above; initially clean |

The owner fetched that exact published commit and added an isolated worktree.
The old checkout was not switched, reset, or cleaned. No PIX `AGENTS.md` or
`PROJECT_STATE.md` was found in the inspected checkout; no ancestor AGENTS file
was found. The README, historical handoff, current API guides and published
owner response were used for intake. Both change-request directory spellings
were searched; the response below is the current PIX request artifact.

The [November 3 owner response](../change_requests/CR-PIDA-PIX-2026-11-03-RESPONSE.md)
describes PR #13 as unmerged at its historical baseline. The refreshed main
includes that work and PR #14. This does not retroactively rewrite its validation
record. GitHub evidence: [main commit](https://github.com/Chanta-Research-Group/PIX/commit/6e9af5ee1b670de39a87be406518fea49dffdfec).

The November 3 response's consumer baseline is `pida.pix.worker.v1`, package `0.5.0`, exact pin
`3205d832d5dcdc6901f916b35496a0c60b657e7a`. Comparing that commit with owner HEAD
under `src/pix` and `pyproject.toml` produced no difference. This is source
compatibility evidence only: the consumer checks both commit allowlist and code
digest. It does not authorize passing the new commit string. Consumers were not
edited or executed in this work slice.

Follow-up intake supersedes any assumption that the Pida alternative is still
unadopted. Pida owner supplied current HEAD
`30fef192b478b1697bb95a22ad7340cf1c485b03`; its published
[profile guide](https://github.com/riesling-29/pida/blob/30fef192b478b1697bb95a22ad7340cf1c485b03/docs/PIX-PROFILES.md),
[acceptance response](https://github.com/riesling-29/pida/blob/30fef192b478b1697bb95a22ad7340cf1c485b03/docs/change-requests/responses/PIX-CR-PIDA-PIX-2026-11-03.md),
and [validation](https://github.com/riesling-29/pida/blob/30fef192b478b1697bb95a22ad7340cf1c485b03/docs/CR-FOLLOWUP-VALIDATION.md)
were then read directly. They record adoption in 0.8.6 of
`pida.pix.profiles/1`: `sequential-prefix/1` and `object-terminal/1`, separately
pinned to PIX `a0831bc0b34fd7feebfba928066b90b114ae531e`. The batch pin remains
unchanged. Their historical Linux evidence reports 28 actual-profile checks,
18 batch checks and 39 explicit Schumpeter file-import checks. Those are producer
records, not this owner's reruns; the cited response accepts the selected adapter
gate but excludes Windows/live operation, arbitrary DAGs and object-current-cut
alignment. Do not duplicate that completed profile-adoption work.

## Verified contracts and compatibility limits

PIX remains generic OCEL/OCPM computation for any supported event-producing
system. Agent, organization and company views are consumer mappings and scopes;
they do not make PIX an execution controller or identity/memory service.

| Need | Existing interface and usable meaning | Boundary that consumers must preserve |
| --- | --- | --- |
| Individual traces | `reconstruct_traces` with explicit `TraceSpec`; `case_traces` and `align_dfg` for completed cases | A shared actor is not sufficient evidence to merge tasks. Completed DFG cost includes required terminal moves, not live violations. |
| Organization/object relationships | Qualified E2O relations; `align_object_log` against an explicit `ObjectCentricPetriNet` | Joint `whole_log` alignment reaches final marking. Exact artifact revision IDs and the model object universe must agree. Actor selection can incorrectly introduce order. Object selection does not filter events. |
| Cross-organization handover | `discover_handover` joins a carrier identity with qualified send/receive relations; grouping can use stable actor attributes | No timestamp pairing or inferred missing receiver. Unmatched links and order conflicts remain visible. A single stable grouping attribute is not temporal membership resolution. |
| Open sequential cut | `OnlineAlignmentStream(OnlineAlignmentSpec).ingest(StreamEvent)` and `.snapshot()` with a Petri net | Always `partial`; prefix upper bound, finite proxy coverage, unresolved final cost while open. DFG models are not accepted here. No general exact-prefix claim. |
| Explicit close | `.close_case(...)` adds final-marking completion to that online witness | Still approximate/`partial`, including zero cost. Close is an observed protocol decision supplied by the host. |
| Completed shared-object scope | `align_object_log` preserves independent selected-object reads and consumes one shared verification event once | No live object-cut termination, arbitrary input DAG, or same-object uncertain ordering support in this profile. Same-object timestamp tie defaults to `unavailable`. |
| Behavior-set context | `measure_object_context`, profile `pix.object_context.binding_prefix.v1` | Terminal observed downset is excluded. It is not a live-next-action verdict or a normalized alignment cost. |
| Resume and corrections | `.checkpoint()`, native `write_result/read_result`, `OnlineAlignmentStream.resume` | Append-only single writer. Duplicate/conflict/gap semantics are explicit; source correction or restart needs a separately identified replay. No distributed CAS or external policy ledger. |

The [API matrix](../user-guide/SCHUMPETER_PIX_CONSUMER_API_MATRIX.md) and
[current-cut profiles](../user-guide/CURRENT_CUT_PROFILES.md) define the full
selection. The current-cut guide is the authority for this proposed next slice.
Relevant implementations inspected are
[online alignment](../../src/pix/case_centric/online_alignment.py),
[object conformance](../../src/pix/compute/object_conformance.py),
[object context](../../src/pix/compute/object_context.py), and
[handover](../../src/pix/compute/handover.py).

Unknown source coverage is not zero deviation. Consumer `UNKNOWN` is distinct
from native `ComputeStatus.unavailable`. Resource caps retain partial or unknown
results; they do not establish conformance. Raw optimal edit cost, proxy upper
bound, joint object cost and context ratio are not interchangeable fitness scores.

The online stream needs independently justified, contiguous zero-based per-case
source sequence. Unknown timestamps are acceptable only when that sequence is
known. Arrival order, event IDs and invented microseconds are not substitutes.
Object alignment derives precedence from selected E2O participation and exact
point timestamps; independent objects remain incomparable even with different
times. These profiles do not establish arbitrary happens-before causality.

Native `pix.analysis-result` 1.3.0 binds operator, source, spec/model and parent
identity as applicable. Online source digest identifies ingestion prefix history,
not canonical OCEL bytes. Retain exact source/build identity, external cut and
coverage, model derivation, policy/grant and adoption references alongside native
artifacts. Digests do not authenticate them. Model/spec/cost/budget changes require
a new identified stream. Authorization and memory applicability remain outside PIX.

## Smallest next executable unit — proposal

Build one two-organization handover mapping fixture on the already adopted
profiles, using the existing [current-cut fixture](../../tests/fixtures/current_cut/README.md)
and handover test as independent semantic oracles. Do not add an engine feature
unless a supported counterexample reproduces an engine defect.

1. Owners first agree the carrier ID, sender/recipient E2O qualifiers, exact
   organization scope and source-sequence provenance for request/response
   observations. Proposed queue/input/response labels alone do not establish
   causal order or organization lifecycle. No new fields are implemented here.
2. Create a synthetic capture with two declared organization memberships,
   exact artifact revisions, independent reads and one shared verification.
   Join send/receive by carrier ID; nearby timestamps with different IDs must
   not join. Missing receive stays unmatched; a shared actor does not merge tasks.
3. Preserve adopted profile invariants through the cross-organization mapping:
   open witness remains `partial` with final cost unresolved, terminal object
   alignment is invoked only for a completed selected scope, and verification
   occurs once with both revisions. Retain original fixture cost expectations;
   do not reinterpret an object's terminal missing-verify cost as a live failure.
4. Keep exact native JSON bytes and hashes; independently check source/model,
   exclusions, scope, stale applicability and unknown order after transport.
   Persona contributes agreed identity/applicability references, not memory
   contents or a PIX-derived authorization claim.

Each consuming owner edits only its repository. PIX supplies the oracle and
reviews computation claims. The fixture's cross-organization source contract
requires coordination; the existing Pida profile adoption does not establish
that new mapping. Native Windows execution of the adopted Pida profile is a
separate next acceptance unit, not implied by this PIX-only Windows test run.

The do-nothing alternative for engine/runtime code is viable: keep the existing
completed batch path while selecting the new profile. No evidence here requires
an engine change. Desktop packaging and Windows/Linux runtime acceptance belong
to their own consumer checks; this Windows run does not certify them.

## Evidence and validation scope

New execution on 2026-11-07, Windows, uv-selected Python 3.13.14, uv 0.11.29:

```text
uv run --no-project --with pytest --with tzdata python -m pytest -q tests/test_current_cut_consumer.py tests/test_pi_hub_consumer.py tests/compute/test_handover.py
61 passed in 2.62s
exit_code: 0
```

The [recorded execution output](evidence/owner-readiness-20261107/focused-tests.txt)
binds this command to owner HEAD `6e9af5ee1b670de39a87be406518fea49dffdfec`.
These existing tests exercise public APIs, native artifact reproducibility,
checkpoint equivalence, order/participation invariants, errors and handover
semantics. This is a focused developer rerun against the source checkout.
Installed-wheel checks, consumer adapters, Linux, desktop UI, live LLM or
Persona execution, and independent review were **NOT_RUN** in this slice.
Historical CI/build records remain historical, not newly executed evidence.
Whole-organization efficiency improvement is **알 수 없음**.

Fixture SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `tests/fixtures/current_cut/input.json` | `e0529cadaae6bb8a2d97a789563e66925eaf3421d081d3a087c9470b45c594a5` |
| `tests/fixtures/current_cut/expected.json` | `8e344d55d9de58703284296e83c45c4e64663746bf1e99253c72e894167e2a34` |

The pstack source was read at `6b0300214a09fd6029cfb7077043125758cd1fd2`:
`poteto-mode`, `swarm`, domain modeling, separating shared state, proving work,
technical writing and unslop. Application here: bounded owner responsibility,
isolated worktree, explicit profile boundaries and executable evidence.
Cursor/cloud agents and model-family routing were adapted to supplied Codex
tools and the inherited model. No cross-family review or global installation
occurred. No additional subagent was spawned for this initial unit.
The [decision log](evidence/owner-readiness-20261107/decisions.tsv) records this
slice. Only the report and its evidence records are added; no runtime, fixture,
consumer pin, remote branch or other application is changed.

## Falsification and validity

The compatibility assessment is valid only for the exact PIX source, fixtures
and selected profile semantics above, as inspected on 2026-11-07. Refresh it when
a source pin, model, adapter contract or scope rule changes. The empty open-PR
list is a point-in-time observation, not a guarantee about later intake.

Withdraw the proposed use of an existing profile if a minimal supported input
disagrees with its independent expected result, resume alters native future
bytes, independent object reads gain an unjustified causal edge, or a shared
event is duplicated. Suspend consumer acceptance if source sequence/revision
evidence cannot be supplied or the required question is exact live arbitrary-DFG
or partially ordered object-cut alignment. Those questions need a narrowed new
contract and oracle. If consumers erase partial/unknown/applicability limits,
their integration fails even when PIX tests pass.

Conclusion: **PASS for PIX owner readiness and this bounded contract intake**.
The existing Pida profile-adapter acceptance remains recorded; the new
cross-organization mapping and live integration remain unaccepted. The next
action is the two-organization mapping/oracle fixture, with no engine change yet.
