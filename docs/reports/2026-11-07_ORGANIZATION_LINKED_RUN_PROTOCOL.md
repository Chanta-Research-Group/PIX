# Organization-linked run metadata: owner protocol proposal

This is a proposed consumer profile, not implemented organization aggregation or
acceptance of a real multi-agent run. PIX remains unchanged. The existing
`schumpeter.pida-admission-root-metadata/1` at Schumpeter `b4025ee18c8c099fd6e00c864117dbad707c1bed`
is root-only and must retain that label.

## Source evidence and scope

Inspected pida `5ea098c0f06e12d0024878446ec3a2705f949934`:

- `src/organization.ts`: OrgSession, OrgTask, OrgAttempt and BatchJoin schemas.
- `src/agent-supervisor.ts`: `getOrganization`, `validateOrganizations`,
  `trackAttempt`, `registerJoin`, `reconcileOrganizations`, native job fields.
- `src/client.ts`: `getOrganization`, `exportAgentJob`, `exportAgentJobOcel`.
- `test/organization.test.mjs`: nested join final-attempt semantics and repair
  receipts; `test/organization-admission.test.mjs`: admitted root/child/continuation.

These source/tests were read, not executed in this design slice. Source hashes
are in the adjacent protocol manifest. Source tests demonstrate intended behavior;
they are not evidence of the forthcoming real multi-agent run.

`getOrganization` returns tasks scoped by `task.orgId`, attempts scoped by those
tasks, and joins scoped by native OrgSession. It has no snapshot revision token.
It can await current acceptance capture before copying mutable state. Repeated
identical reads establish observed stability, not a transactional snapshot across
organization, jobs and observation journals.
The pida owner separately confirmed the absence of a public snapshot token and
the initial-root/final-child distinction during this coordination slice.

## Smallest proposed profile

Proposed name: `schumpeter.pida-organization-linked-runs/1`. It produces one
metadata index linking separately computed native per-run results. It does not
merge OCELs, synthesize Organization/Message events, calculate a global DFG,
or claim whole-organization conformance. Keeping root-only analysis is the valid
no-change alternative until the following joins and coverage are supported.

1. Resolve current registered host, principal, source-specific approval and
   reservation through the reviewed admission source API. Bind full original
   receipt and observed binding revision. Do not grant execution permissions.
2. Fetch the exact native OrgSession and verify owner, rootTaskId and receipt
   recipient. The admission receipt always anchors the original root job and
   root attempt. It must not be rewritten to the latest continuation/repair.
3. Enumerate expected membership only through `OrgTask.orgId == OrgSession.id`,
   each task's ordered attempt IDs, and `OrgAttempt.taskId/jobId`. Validate
   attempt number/kind, uniqueness and the reverse membership. Participants are
   permitted agent identities, not evidence that they executed. Never enumerate
   all jobs of a participant to fill this set.
4. Read each exact native job through its task's agent. Require trusted owner,
   task.agentId == job.agentId, task.id == job.organizationTaskId,
   attempt.id == job.attemptId and attempt.jobId == job.id. The child agent is its
   own identity, not the root binding's agent. Preserve job.parentJobId when
   present. Missing or external parents are unresolved lineage, not invented roots.
5. Validate BatchJoin org/task/parent references. `required` and `optional`
   contain assignment job IDs. A result's `jobId/attemptId` may be a later child
   continuation or repair; require the same child's OrgTask, not assignment-job
   equality. Preserve result/input digests, runId, join revision/status and
   continuationJobId. Validate continuation job joinId/joinRevision against the
   declared revision. Do not require parentJobId alone to encode continuation:
   the producer may inherit the original parent's parent instead.
6. For each terminal job with native run/session, validate and export through the
   actual hash-bound producer tools. Preserve source_event_id, source_id, original
   time and per-source/session/run sequence. Runtime bundle task_id is job.id;
   native OrgTask and OrgSession remain separate index facts. Pi session is never
   an OrgSession alias. Run the already supported typed trace/DFG/OCDFG and
   Run/run execution/variant operators independently for each component.
7. Re-read job metadata, bundle/export cuts, organization membership/joins,
   source binding and authorization. Record before/after hashes and observation
   intervals. Changed cuts are partial/unstable; do not keep changing membership
   until a convenient complete answer appears. A bounded retry creates a new
   capture attempt. Even equal reads retain `snapshot_atomic=false` until a
   producer snapshot contract actually exists.

## Index, coverage and privacy

The versioned index needs source/host/principal/reservation/receipt identity,
full binding and source/schema/tool/engine/spec hashes, exact native OrgSession
and membership hashes, all expected task/attempt/job IDs, typed parent/join links,
and one component record per expected job. Components bind PiSession/run,
source journal identity, first/last original sequence, event count, bundle and
OCEL digests, limits, capture hashes and native artifact parent closure. Keep
original source metadata identity distinct from PIX canonical source identity.

Component states should distinguish captured terminal, not started/no run,
nonterminal, export unavailable, access unavailable and unstable cut. Integrity
contradictions (wrong owner/task/attempt, conflicting duplicate event identity,
receipt replacement, fabricated native ID) fail the affected mapping; they must
not be softened into ordinary missing coverage. Source-level revoked access
blocks publication/serving; partial diagnostics must not expose denied bodies.

Report membership stability separately from component availability, bundle
complete, manifest limits/UNKNOWN verification, exporter limits and native result
status. A missing optional child still makes observation coverage partial even
when a runtime join is ready. A terminal org/root does not prove all child
journals are exported. An unavailable run contributes **unknown**, not zero.
For this first profile, use `coverage=partial`, `snapshot_atomic=false`, and list
captured/expected jobs; do not label it a complete organizational trace.

Counts remain per run. Summed occurrences are explicitly sums of captured
component occurrences; they are not unique organization events or object counts.
If presenting a distinct count, use producer source-event identity and verify
identical metadata on overlap; never silently consume duplicates or conflicting
copies. Agent/Session objects can recur across runs, so object counts cannot be
blindly summed. No cross-run ordering, timestamp offsets, arbitrary event-ID
tie-breaks, or efficiencies can be inferred from this index. Native joins are
workflow dependency evidence, not proof of model input consumption or logical
message delivery. Handover remains unavailable for this profile.

Persist a closed metadata vocabulary only. Exclude org.goal, job.input,
latestText/result text, join continuation prompt and Persona descriptor/body.
Retain existing artifact/evidence references and exact revision digests without
fetching artifact bytes. Full response hashes can be computed transiently; hashes
are not authentication and private metadata remains local. Any schema/tool,
membership, binding, grant or component-cut change creates a new applicability
identity. Do not conflate artifact acceptance receipts with PIX conformance.

## Minimal visible row contract

Use a stable row key `(trusted_source_id, host_id, native_org_session_id,
native_job_id)`, with exact native agent ID, OrgTask ID, attempt ID/number/kind,
Pi session/run (or explicit missing), and component artifact links. Source identity
and host prevent collisions between unrelated installations. Display a supplied
agent label only alongside its native ID; names are not join keys.

The original receipt job is labelled **initial root**. A child initial job is
labelled **child**, with its actual parentJobId and parent row link. A continuation
or repair is labelled by attempt.kind, with its OrgTask link and explicit
joinId/revision/parent or predecessor relation where evidenced. Do not present
every root-task attempt as the admission root. Nested join rows link both the
assignment job and resolved final child job. No relation should be generated from
timestamps or indentation alone.

Show source job status, capture state, individual PIX result status and coverage
limits separately. An expected child without an export keeps a visible row and
an unavailable/unknown reason; it never disappears from the denominator. Display
captured/expected job counts and `partial, non-atomic` at the index level. A row
can link computed DFG while still showing manifest UNKNOWN or incomplete evidence.
If no narrow index implementation fits the package schedule, deliver this same
row mapping as a local metadata report linking the existing per-run artifacts;
that fallback makes no new desktop aggregation claim.

## Minimal review vectors before real use

The accompanying JSON contains symbolic proposed vectors, not actual runtime
evidence. Minimum positive case: initial root A0, child B0, root continuation A1
with an explicit join; root receipt continues to identify A0. Nested case B1
settles B0's task: join result points B1 while assignment remains B0. Existing
producer tests cover this distinction, but consumer matching requires its own
actual exporter proof. A real multi-agent label needs native observed runs for
at least two distinct agent IDs, not registration alone.

Negative requirements: unrelated same-agent job excluded; missing child partial;
wrong owner/OrgSession/attempt rejected; admission root substitution rejected;
changed membership or bundle cut unstable; repeated source-event conflict rejected;
equal timestamps remain unchanged and unavailable when the native operator
requires strict order; manifest UNKNOWN/incomplete survives successful execution;
join revision changes invalidate the index; unstarted/cancelled run contributes
no fabricated event. Never manufacture a real multi-agent fixture from the
earlier one-agent trace.

Next consumer unit: capture an authorized actual scripted root/child/continuation
graph with these APIs, preserve each native export, and prove linked per-run
results and the missing-child/unrelated-job negatives. A subsequent real model
case and frozen desktop invocation are separate acceptance evidence. No new model
call is authorized by this proposal itself.

Validity ends when the cited producer/consumer contract changes. Withdraw this
proposal if current APIs cannot establish owner-scoped membership or component
identity, if a real snapshot guarantee contradicts the source reading, or if
metadata-only projection cannot exclude bodies. Organizational improvement is
**unknown**. Conclusion: the smallest supportable next profile is a deliberately
partial organization index of verified per-run results, pending consumer proof.
