# Conversation logs, handovers and observation precision

Implemented for [#9](https://github.com/Chanta-Research-Group/PIX/issues/9),
[#10](https://github.com/Chanta-Research-Group/PIX/issues/10) and
[#11](https://github.com/Chanta-Research-Group/PIX/issues/11).

## Quick start

Run the synthetic example from an installed PIX environment:

```bash
python examples/chat_handover_demo.py --output /tmp/pix-chat-demo
```

It imports conversations, creates a carrier-based handover network, and evaluates
an acknowledgement within ten minutes. Two observations in the same minute
produce one handover link and one **indeterminate** timed obligation. Four native
result JSON files retain their source identities and evidence.

```python
from pix.api import (
    HandoverSpec, TimePrecision, TraceSpec, discover_handover, reconstruct_traces,
)

minute = TimePrecision(60_000_000)
traces = reconstruct_traces(
    log, TraceSpec("message", tie_policy="concurrent", time_precision=minute)
)
network = discover_handover(log, HandoverSpec(time_precision=minute))
```

## #9: timestamps are observations, not inferred order

`TimePrecision(g)` interprets a recorded timestamp `t` as `[t, t+g)`.
The special value `g=1` preserves existing exact microsecond observations.
PIX does not round timestamps down or create offsets. An optional `attribute`
selects a positive integer microsecond width on each event; missing or invalid
values fail explicitly. Timezone-aware source timestamps remain required.

`TraceSpec(..., tie_policy="concurrent")` groups overlapping intervals within each
selected object's qualified E2O events. Overlap components are transitive.
`TraceEvent.order_group` identifies a group; the tuple's deterministic display
order inside that group is **not** temporal or causal evidence. Event IDs, source
positions and E2O qualifiers are retained; positions do not override time evidence.

`ConstraintSpec.time_precision` inherits the input trace's declaration when omitted.
An explicit different declaration is invalid input. Timed-response witnesses expose
elapsed lower/upper bounds and may be `indeterminate` because order is unknown or
the time window intersects the observation interval. `first` considers all possible
first responses in an unordered group; `any` accepts a definitely fulfilling
candidate. Closed observations without a target are violated; open prefixes keep
their existing pending/deadline semantics. Untimed response/precedence also retain
unknown order rather than using the display order as evidence.

`RuleEvaluation` exposes indeterminate activation/object counts and fulfillment
ratio bounds. Indeterminate outcomes are computed observations with diagnostics;
pending open-prefix obligations still make the envelope partial. Ratio bounds
use all observed activations and do not predict future open-prefix outcomes.

`measure_temporal` reports interval samples and exact rational bounds for summary
means/medians. An uncertain duration or median has no fabricated point estimate.
Within a concurrent group it measures unordered pair separations (lower bound 0);
between adjacent groups it retains all possible boundary pairs. Activity labels
orient unordered pairs deterministically for display, not as directed succession.
These population choices are disclosed in `unordered_temporal_pairs`. Concurrent
measurements above 100,000 possible pair occurrences fail with an explicit limit
diagnostic; narrow object/qualifier selection rather than accepting a prefix.
Service measurements require `start_attribute`; insufficient precision is reported
as `service_below_precision` with partial service coverage. Trailing anchors have
no finite upper bound, represented by `None`.

DFG/OCDFG, process discovery, alignment, replay and prefix precision reject
concurrent traces until those operators have explicit partial-order semantics.
Callers may still choose the existing `reject` or lexical `event_id` policy.

## #10: qualified carrier joins across turns

`discover_handover(log, HandoverSpec())` joins all send/receive observations sharing
the selected carrier object ID. Defaults select `message` objects with `sent` and
`received`, and `employee` actors with sender/receiver or fallback `actor` roles.
An explicit directional role takes precedence over the shared fallback qualifier
in carrier mode. This preserves original authorship on an incoming message while
identifying the actual receiving endpoint.

The operator never joins by timestamp ordering. Earlier receives remain linked,
with `order_conflicts` only when interval bounds establish a conflict. Unmatched
event IDs remain in a computed result with `unmatched_handover_events` diagnostics.
All selected send/receive events are counted once, and each link retains E2O
evidence. Repeated observations of one carrier produce all send/receive
combinations, not an inferred one-to-one delivery history.

`multi_receiver="each"` expands explicit recipients; `"reject"` rejects fan-out.
`mode="event_roles"` links sender/receiver objects on a single event without a
receive observation; latency is unavailable. Self links are optional, excluded
counts are disclosed, and `max_links` rejects the whole request rather than
returning a silently truncated network.

`group_by_object_attribute` requires one stable string value for every selected
actor. Missing or changing group membership fails explicitly; PIX does not choose
an implicit historical snapshot. Group edge link totals equal actor edge totals.

This differs from case-centric `discover_social_network(metric="handover")`,
which counts successive resources within one case. The new operator follows
qualified carrier objects across cases/turns. It does not rank actors. A dedicated
viewer graph adapter is optional future work; native JSON is supported now.

## #11: declarative JSONL/record adapter

The public facade exports `MatchRule`, `CarrierRule`, `ChatLogMapping`,
`ChatImportResult` and `import_chat_log`. Inputs are generic mappings or JSONL
paths; product-specific transport parsing and semantic text classification are
outside this adapter.

Rules support dotted fields, equals/prefix/regex/present operations, and AND
conditions. The first opener determines the turn trigger. The first activity rule
determines activity, falling back to the opener label. Rule order and all mapping
options contribute to `mapping_digest`; callbacks are not accepted. `rule_hits`
counts actual opener, activity and carrier rule applications by label (reuse of a
label aggregates counts).

Each conversation is processed in its unique integer source positions. Observed
times must not decrease. Missing times anchor to the previous observed source
record, retaining `time_lower`, optional `time_upper` from the next observation,
`time_basis` and `position`. No artificial microseconds are introduced. A leading
record without an observed anchor fails. A trailing anchor has no upper bound;
PIX does not substitute the anchor as an exact time. Use the same declared
`TimePrecision` in downstream analyses. Per-record precision attributes are
retained, alongside `time_granularity_microseconds`.

Records without classification or before any opener follow `unmatched_activity`:
error, drop with explicit counts, or an `unclassified` activity/turn. The result
always reports unclassified, dropped, anchored and turn counts. `max_records`
bounds ingestion; duplicate positions and malformed inputs fail atomically.

Object roles are `request/request`, `channel/room`, `employee/actor`, and carrier
`sent/received`. Explicit recipients have `employee/receiver`. Namespaces avoid
cross-type ID collisions. Incoming records can identify the sender as their author:
`CarrierRule.receiving_actor_field` explicitly identifies the receiver and defaults
to `conversation_id`; change it for logs whose conversation ID is not an actor ID.

Prefer `pair_key="explicit_id"` with a source message ID. The opt-in
`sender_receiver_order` pairs the nth send and nth receive for the explicit endpoint
pair. This is a declared matching convention, not causal inference. Multiple source
conversations making that endpoint ordering ambiguous are rejected. Unpaired sends
and receives retain their carrier objects for handover diagnostics.

By default the output retains no message text, only SHA-256 text digests.
`text_digest="none"` disables these as well; `retain_text=True` is an explicit
opt-in. A digest is not anonymization for guessable short messages. Input errors
do not echo malformed record contents.

For nonempty logs, `pix:chat_mapping_digest` is a canonical event attribute. It
survives OCEL export/reimport, changes the source identity when rules change, and
appears in result provenance diagnostics as `source_mapping_digest` with an
`("mapping_digest", digest)` location. `ChatImportResult.mapping_digest` is also
available for empty/dropped populations. Full rule text is not copied into OCEL.

## Persistence and compatibility

Native result documents now use `pix.analysis-result` version **1.3.0**. The reader
continues accepting 1.0/1.1/1.2 documents, including missing newly optional fields.
Only explicitly declared optional fields may be omitted; unknown fields remain
errors. New handover payloads use the `handover-network` result type.

Default `time_precision=None` fields are omitted from computation identity, so
existing default computation IDs and values remain unchanged. Regression fixtures
were generated from unmodified main `71822445`, including trace, constraint and
temporal results. Explicit precision or concurrent policies have their own IDs.

Validation commands:

```bash
python -m pytest -q tests/compute/test_time_precision.py tests/compute/test_handover.py tests/tabular/test_chat_log.py
python -m pytest -q
```
