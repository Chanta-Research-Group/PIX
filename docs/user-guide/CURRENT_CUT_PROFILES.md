# Current-cut and shared-event consumer profiles

This is a selection of existing PIX public APIs, verified against the synthetic
fixture in [current_cut](../../tests/fixtures/current_cut/README.md). It is not a
new worker protocol. The [owner response](../change_requests/CR-PIDA-PIX-2026-11-03-RESPONSE.md)
records the Pida request, source pins and remaining integration work.

## Select a model and a question together

| Question | Exact public input / call | Output / termination | Limits and selection |
| --- | --- | --- | --- |
| Completed case relative to an accepting DFG | `pix.event_log.case_traces(CaseLog)`; `pix.case_centric.sequence_alignment.align_dfg(traces, DFGAlignmentModel, DFGAlignmentSpec)` | `ComputationResult[DFGAlignmentSet]`; consumes the full case and reaches a graph end; minimum raw insertion/deletion cost when `optimal` | `max_states`; `search_limit` is `partial` with unknown cost and a lower bound. Not a current-prefix API. |
| Incremental, explicitly sequenced case relative to a Petri-net path proxy | `pix.case_centric.online_alignment.build_online_alignment_proxy(OnlineAlignmentSpec)`; `OnlineAlignmentStream(spec).ingest(StreamEvent)`; `.snapshot()` | `ComputationResult[OnlineAlignmentSnapshot]`; open cost is `model_prefix_alignment_upper_bound`; only `.close_case(...)` adds final-marking completion | **Always `partial`**, including a zero-cost witness. Finite proxy, lookahead, decay, beam and expansion limits do not prove optimality or language completeness. |
| Resume that incremental profile | `.checkpoint()`; `pix.results.write_result/read_result`; `OnlineAlignmentStream.resume(checkpoint)` | Native `ComputationResult[OnlineAlignmentCheckpoint]`; restores the saved model/spec, protocol and witness state | Append-only, single writer; not a mutable source ledger or distributed CAS. Unsupported version/changed identity is rejected. |
| Joint, completed object scope with shared events | `pix.api.align_object_log(OCEL, ObjectCentricPetriNet, ObjectAlignmentSpec)` | `ComputationResult[ObjectAlignment]`; one event downset and joint marking; requires exact final marking | `whole_log` only; `max_states` / `max_bindings`; same-selected-object equal times default to `unavailable`. No arbitrary input DAG or current-cut termination option. |
| Observed next-binding behavior sets | `pix.api.measure_object_context(OCEL, ObjectCentricPetriNet, ObjectContextSpec)` | `ComputationResult[ObjectContextMetrics]`, profile `pix.object_context.binding_prefix.v1`; exact ratio numerators/denominators where available | The terminal observed downset is **excluded**. This is not an evaluation of what must happen next at the live cut, or normalized edit cost. Separate log/context/binding budgets. |

All types in these calls are public. `StreamEvent` and `StreamingSpec` live in
`pix.case_centric.streaming`. Model constructors live in `pix.contracts.models`.
`OnlineAlignmentSpec` requires a **PetriNet**, not a `DFGAlignmentModel`. Native
result format is `pix.analysis-result` 1.3.0; the listed operators use version
1.0.0. `pix.model` 1.0.0 stores the Petri net/OCPN, with declared origin.

The example's linear DFG and four-transition Petri net are independently
specified to accept exactly `request → edit → test → deliver`. Their matching
language is evident for this one chain. This does **not** establish a generic
conversion, concurrency inference, or equivalent numerical guarantees. A DFG
may have cycles and recombinations; a bounded finite path proxy may omit them.
A consumer adopting the online profile must obtain a separately identified,
compatible model and record its derivation, costs and proxy coverage.

## Executed comparison

| Synthetic input | Native outcome | Interpretation |
| --- | --- | --- |
| `request → edit`, batch DFG | `computed / optimal`, cost 2 | Minimum terminal completion edits: `test` and `deliver`. Not two current violations. |
| Same input, online still open | `partial`, cost 0; `final_cost_unresolved=True` | Executable prefix witness; future completion is pending. |
| Same input, explicit close now | `partial`, cost 2; final unresolved false | An accepting witness includes the two missing model moves; still approximate. |
| Append `test → deliver`, then close | `partial`, cost 0 | Accepting witness for this model; not business acceptance. |
| Completed trace with extra `review` | batch `computed / optimal`, cost 1 | Model-relative deviation. A policy can permit or require review. |
| Batch `max_states=1` | `partial / search_limit`, cost null | No optimal cost invented. |
| Online proxy node budget admits no path | `unavailable / proxy_unavailable` | Not proof that the model is unreachable. |
| Two independent artifact reads between shared start and verify | joint `computed / optimal`, cost 0; 4 synchronous moves | Both reads remain incomparable, verify is consumed once with both exact revision IDs. |
| Same selected artifact has a time tie | `unavailable / ambiguous_event_order` | No event-ID or arrival-order workaround. |
| Joint object log ending before verify | `computed / optimal`, cost 1 | This operator still requires terminal completion. Do not call the missing verify a current failure. |
| Context metric on that cut | terminal prefix count 1; final cut absent from scored contexts | Earlier observed contexts are measured; live-next-step conformance is not supplied. |

The object fixture's model is deliberately permissive: each artifact may take
either read label before joint verification. It is an ordering/participation
example, not a policy requiring a particular reviewer, quality decision or read
assignment. Revision IDs are opaque exact identities, not verified file hashes.

## Ordering and scope are supplied evidence

The online profile requires contiguous zero-based **per-case source sequence**.
It accepts an unknown timestamp when that sequence is independently justified.
Do not use arrival order, sorted IDs or artificial microseconds to manufacture
that sequence. Missing sequence positions are rejected atomically. An omitted
event that the producer conceals by renumbering cannot be detected by PIX; retain
source coverage/exclusions outside the native result.

The object profile derives precedence only from selected-object event times and
selected E2O qualifiers. Independent selected objects remain incomparable even
when their timestamps differ; one chosen optimal witness is not new causal
evidence. It does not consume arbitrary happens-before edges, O2O causality,
`TimePrecision`, or uncertain interval semantics. Supply exact point times for
this profile. `tie_policy="event_id"` is an explicit convention, inappropriate
when the required meaning is unknown order. Same-object concurrent/anchored or
interval-uncertain observations remain outside this selected profile; generic
OCEL validation alone does not establish their ordering compatibility.

The example selects `artifact_revision` / `uses`, excluding the shared agent's
actor relations. This prevents the agent from ordering unrelated artifact
events. **Object-type selection is not event filtering:** `whole_log` retains
even an event with zero selected participants, which may yield a log deviation.
Pida must create an authorized task/event snapshot before calling this operator.
Do not merge tasks through one common agent or duplicate shared verification as
independent cases. The supplied OCPN object universe and all initial/final
markings must match that snapshot; changing an artifact revision without the
model produces `invalid_input`.

## Checkpoints, corrections and identities

| Transition | Selected online contract | Consumer action |
| --- | --- | --- |
| Append next event | supported; updated native prefix digest and computation ID | Keep exact source sequence and cut reference. |
| Identical retry in retained dedup window | receipt `duplicate`, unchanged checkpoint | Do not treat it as a second observed event. |
| Conflicting event ID/sequence | `ValueError: duplicate_conflict`, no state mutation | Correct the source ledger and recompute a new cut; do not mutate checkpoint. |
| Retry beyond dedup window | `expired_sequence` or membership diagnostic, not silent acceptance | Reconcile retained source facts. Bounded membership filters can conservatively reject collisions. |
| Missing sequence / append after close | explicit error, no state mutation | Resolve missing evidence or start a separately declared generation. |
| Source restart or correction | no built-in generation/CAS transaction | Allocate new stream/generation identity, replay justified facts; retain old results. |
| Model, proxy, costs or budget change | part of spec/computation identity; not interchangeable | Build a new stream; never relabel an old result as applicable to the new model. |
| New policy/grant/artifact adoption revision | not a PIX checkpoint field | Bind/check in Pida/Persona; invalidate applicability externally. |

`source_digest` in an online result is the ingestion prefix digest, **not** the
canonical OCEL digest. Interleaving operations across cases contributes to this
history identity. The computation ID binds operator/version/source/spec and
parent IDs, including the saved model and stream ID. The checkpoint's additional
state digest and native document digest protect different serialized content.
They detect changes, not authenticity; they do not establish the actor's grants,
external cut revision, all source evidence, policy revision or package build.
Store the exact package source/wheel identity alongside the native artifact.

Native proxy/snapshot/checkpoint results have no invented parent chain. The
bundle retains all artifacts; Pida may relate their external cut/model refs in
its own contract. Derived DFG result parent IDs resolve to the included trace
results. Object result specs bind a semantic model digest; both native models
are supplied separately in the fixture.

Existing `RevisableCaseStream` / `OCRevisableStream` support a separate retained
fact correction/retraction workflow (see [the guide](MODELS_AND_W4_GUIDE.md)).
They do not patch `OnlineAlignmentStream`'s checkpoint or compute its alignment
incrementally. Their existence is not evidence of a drop-in revision protocol.
Those APIs were inspected, not newly integrated in this patch.

## Budgets and metric comparisons

Online bounds include proxy trace/step/node/attempt limits, lookahead,
`max_states_per_case`, `max_expansions_per_event`, witness history and ingestion
case/activity/dedup limits. This example uses capacity rejection rather than
evicting open cases. An eviction-enabled consumer must preserve omitted-case
diagnostics. Execution time, input/output byte limits and process cancellation
belong in the host; these APIs do not promise a wall-clock deadline.

DFG raw optimal edit cost, online witness upper bound, event/object-weighted
joint alignment cost and object-context ratios have different definitions.
Compare only an explicitly matched language, costs, population and termination
question. Do not rename them a common normalized fitness score or rank agents
with incomparable values. Search caps preserve unknown cost/coverage; zero
denominators and absent observations do not establish zero violations.

Exact live-prefix alignment for the consumer's existing arbitrary DFG,
incremental partially ordered object current-cut alignment, and arbitrary
explicit-DAG input are **not supplied by this selection**. Do not claim they
exist by converting labels or sorting events. Further engine work needs the
chosen semantics and an independent oracle; the current batch path can continue.
