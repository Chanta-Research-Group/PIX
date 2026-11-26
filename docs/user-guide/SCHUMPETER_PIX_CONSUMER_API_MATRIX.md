# Schumpeter PIX Consumer API Matrix

Date: 2026-10-25. Engine baseline verified: `48fe7eb67388cda1144c5bba93adbfe00933ab1c`,
PIX `0.5.0`, canonical format V1, native result format `1.3.0`.
This readiness patch preserves that engine source. The final fixture/tooling
commit, actual environment and test evidence are recorded in the
[readiness report](../reports/2026-10-25_SCHUMPETER_PIX_READINESS_REPORT.md).

`CR[T]` means `ComputationResult[T]`; `CTX` means `ComputationContext`.
Rows below were exercised through the [consumer fixture](../../tests/fixtures/pi_hub/README.md)
and the existing focused suites. They describe tested synthetic scope, not a
completed Schumpeter deployment. Each row's verified engine commit is the full
baseline SHA above. Examples below are executed by
[`adapter_contract_demo.py`](../../examples/adapter_contract_demo.py), unless a
specific test/demo is named.

## Public calls and contracts

| API name / public import | Input → output | Required options / supported scope | Result status / known limitations | Minimum reproducible call |
| --- | --- | --- | --- | --- |
| `pix.ocel.build` | Typed event/object declarations and records, E2O/O2O iterables → `BuildResult` | Explicit IDs, types, qualifiers and aware times | `.valid`, `.report`, `.candidate`; `.ocel` only when valid. Constructors can raise for invalid primitive values. No inferred relationships or repairs | `build(event_types=..., object_types=..., events=..., objects=..., e2o=..., o2o=...)` in `build_snapshot` |
| `pix.ocel.validate` | OCEL → `Report` | Dataset-wide references, declarations, attribute semantics | `.valid`, `.errors`, `.warnings`; not capture completeness or authenticity | `validate(log)`; F02 invalid-reference cases |
| `pix.api.read_ocel` | Source, optional `format` → OCEL | JSON/XML/SQLite verified; explicit format when necessary | Returns valid OCEL or raises `OCELImportError`. For stage diagnostics use `import_ocel`. Reader can assume UTC for naive input and disclose that in import metadata; the example instead requires aware source times | `read_ocel(path)` on each exported snapshot |
| `pix.api.import_ocel` | Source, optional `format` → `ImportResult` | Same import contract, structured diagnostics | `ImportStatus`: valid/unavailable/unsupported/syntax_invalid/schema_invalid/mapping_invalid/semantic_invalid. Inspect `.import_issues`, semantic report and candidate before consumption | `import_ocel(path)`; `tests/ocel/test_reader.py` |
| `pix.api.export_ocel` | OCEL, path, required `format` → `ExportResult` | json/xml/sqlite; overwrite=False by default | Successful `published` plus semantic/round-trip evidence; `ExportError` on failure. `reference_schema=not_run` is not a reference-schema pass. Noncanonical import metadata is outside interchange | `export_ocel(log, path, format="json")` |
| `pix.ocel.canonical_digest` | OCEL, optional canonical version → `CanonicalDigest` | Canonical semantic identity | Use `.identifier` for CR.source_digest comparison; `.hexdigest` for raw hash. Invalid OCEL raises. Not original file bytes or source authentication | `canonical_digest(log).identifier` |
| `pix.api.reconstruct_traces` | OCEL/CTX, `TraceSpec` → `CR[TraceSet]` | object_type required; qualifier/tie/time policy explicit | computed for valid selected population; unavailable for unknown type/order ambiguity; invalid_input for invalid input/precision. Empty objects remain represented | `reconstruct_traces(log, TraceSpec("task", qualifiers=("task",)))` |
| `pix.api.discover_executions` | OCEL/CTX, `ExecutionSpec` → `CR[ExecutionSet]` | method required; choose object/qualifier scope and leading type if applicable | E2O-based extraction; order can be unavailable/partial. Shared actors can connect unrelated tasks if selected. No O2O connectivity, no TimePrecision/concurrent option | `discover_executions(log, ExecutionSpec("connected_components", object_types=("task",)))` |
| `pix.api.discover_variants` | `CR[ExecutionSet]`, `VariantSpec` → `CR[VariantSet]` | Complete extraction and supported ordered graph, explicit search budget if changed | computed exact groups; unavailable for partial/ambiguous parent or exhausted search; invalid_input for invalid parent/graph. Not a TraceSet API or trace value_counts catalog | `discover_variants(executions, VariantSpec())` |
| `pix.api.discover_dfg` | OCEL/CTX, `TraceSpec` → `CR[DirectlyFollowsGraph]` | Explicit object/qualifier and supported tie policy | Exact sequence counts/evidence; concurrent unsupported. Saved as OCDFG's parent artifact | `discover_dfg(log, TraceSpec("task", qualifiers=("task",)))` |
| `pix.api.discover_ocdfg` | OCEL/CTX, `OCDFGSpec` → `CR[ObjectCentricDFG]` | Nonempty object_types; qualifiers and tie policy | Per-type graphs with event-pair/object/occurrence counts. No O2O-derived edges. concurrent → invalid_input; no time_precision field | `discover_ocdfg(log, OCDFGSpec(("task",), qualifiers=("task",)))` |
| `pix.api.evaluate_constraints` | `CR[TraceSet]`, `ConstraintSpec` → `CR[ConstraintEvaluation]` | Rules, open/closed observation, time policy inherited or matching | computed can contain violations/indeterminate; pending makes partial. Incomplete upstream population is unavailable. Empty activation population has no invented fulfillment ratio | `evaluate_constraints(traces, ConstraintSpec((TimedResponseRule("ack", "sent", "received", 0, 60000000, "first"),), "closed"))` |
| `pix.api.measure_temporal` | OCEL/CTX, `TemporalSpec` → `CR[ObservedTemporal]` | object_type, qualifier/tie/precision/weighting; start_attribute for service time | Conservative interval samples, rational summaries. No point estimate when uncertain. Service status is separate; absent start does not imply zero service time | `measure_temporal(log, TemporalSpec("task", qualifiers=("task",)))` |
| `pix.api.TimePrecision` | Positive integer μs, alignment="floor", optional attribute → immutable spec | `None`/1 preserves exact-point semantics; g>1 means [t,t+g), no rounding | Not a result/status. Per-event selected width must exist and be valid. A timestamp printed to seconds is not automatically a one-second bucket | `TimePrecision(60000000)`; F03/F04 tests |
| `pix.api.discover_handover` | OCEL/CTX, `HandoverSpec` → `CR[HandoverNetwork]` | Choose carrier/actor types, send/receive roles, multi_receiver, grouping/time policy | computed can include unmatched/conflicts. Carrier-ID joins, never time pairing. Repeats produce all observed combinations. event_roles has no observed receiving timestamp | `discover_handover(log, HandoverSpec(actor_object_type="agent"))` |
| `pix.api.import_chat_log` | JSONL path or records, `ChatLogMapping` → `ChatImportResult` | Serializable opener/activity/carrier rules, source positions, anchor policy | ImportStatus, `.valid`, `.candidate`, `.import_issues`, mapping digest and counts. Not a bot-specific transcript parser. Missing explicit IDs do not silently fall back to ordering | Existing `examples/chat_handover_demo.py`; F08 tests |
| `pix.api.result_json_bytes` / `write_result` / `read_result` | CR → bytes/file → CR | Supported operator/spec/payload and result schema | Validates identity and envelope; raises on unsupported/tampered documents. Native 1.3.0 writes, legacy 1.0–1.2 reads | Each of the eight native artifacts is round-tripped and repeated byte-for-byte |

## Time, relation and coverage requirements

The producer owns the time interpretation. For minute observations use explicit
TimePrecision consistently across trace, temporal and handover computations.
ConstraintSpec inherits the trace's declaration; contradictory declarations fail.
For unobserved in-turn timestamps, the existing non-chat-specific representation
is supported by the current engine and tested in F04:

| Event representation | Meaning |
| --- | --- |
| aware Event.time, no precision/anchor | Exact recorded point; only use when justified |
| TimePrecision(g>1) | [Event.time, Event.time+g), conservative enclosing elapsed bounds |
| `time_basis="anchor_previous_observed"`, `time_lower` datetime equal to Event.time, optional `time_upper` datetime ≥ lower | Explicit anchored interval; missing upper means unknown/unbounded upper |
| missing/invalid lower, reversed bounds | Explicit failure; never fill from wall clock or source position |
| no anchor at all | Not a valid timed OCEL event; preserve raw null externally and hold/exclude explicitly |

Declare time attributes as OCEL `ValueType.TIME` and time_basis as STRING.
This compatibility convention preserves current behavior; no new bounds-selector
API is needed by the verified fixtures. It does not infer an anchor or certify
the producer's evidence. Original source nulls and projection exclusions remain
outside PIX. General arbitrary interval contracts remain a conditional backlog.

Concurrent groups do not establish causal order. DFG/OCDFG, discovery, alignment,
replay and prefix precision explicitly reject concurrent input. Execution variants
also require supported order; ExecutionSpec/OCDFGSpec cannot represent every
precision contract. Do not remove precision or select lexical event_id ordering
to bypass this boundary. The exact fixture is the positive sequential example;
uncertainty counterexamples deliberately expect refusals or indeterminate results.

Handover evidence fields are `event`, `object`, `qualifier`; links reference the
original qualified E2O facts. Unmatched counts concern selected carrier events,
not every actor event. Without a carrier ID, use explicitly declared event_roles
only if that is the actual observation, or report the source limitation.
Group attributes must have a single stable string value per selected actor.
Unknown/changeable membership is not silently assigned a current group.

## Mapping and result lineage

Native result fields are `operator_id`, `operator_version`, `source_digest`,
`spec`, `status`, `value`, `issues`, `computation_id`, `parent_computation_ids`.
Package/build version, wheel hash and artifact location belong to the consumer's
execution record. Computation identity includes the operator/spec/parents, not
the full Python package binary. Pin both the code and its installed artifact.

The example puts its explicit, caller-owned `mapping_digest`, source ID and
source-event ID in canonical event attributes. These survive all three I/O
round-trips and change the canonical identity when the mapping changes. PIX does
not automatically interpret that generic attribute as a dedicated CR field.
`run-record.json` joins the mapping with native results via source identity and
links every parent artifact. No new product provenance API is required here.

The chat adapter retains `pix:chat_mapping_digest` and exposes
`ChatImportResult.mapping_digest`; some results also carry `source_mapping_digest`
diagnostics. Derived results can rely on parent lineage rather than repeat that
diagnostic. Empty/all-dropped populations have no event attributes: keep the
import result and mapping record, not only the empty OCEL digest. The existing
`mapping_fingerprint` for tables uses its own versioned format. Never conflate
these hashes or store computation-changing semantics only in noncanonical
OCELImportInfo.

Chat policies are spelled `error`, `label_unclassified`, `drop_with_count`.
The adapter exposes unclassified/dropped/anchored/turn/rule-hit counts; unmatched
send/receive counts come from handover analysis. Text is not retained by default;
SHA-256 text digest is the default and can be disabled with text_digest="none".
The optional sender_receiver_order convention is not proof of actual delivery.

`computed` means the declared calculation completed; it does not mean workflow
success, a complete source population, trusted verification or approval. UNKNOWN
is a consumer observation label, not interchangeable with ComputeStatus.unavailable.
Do not join unrelated unknown task/session IDs into a single real object. Record
capture coverage, held/excluded counts, open/closed policy and denominator outside
the native result, using Schumpeter's existing storage/manifest contract.

## Reproduce and hand off

```bash
python -m pytest tests/test_pi_hub_consumer.py tests/compute/test_time_precision.py tests/compute/test_handover.py tests/tabular/test_chat_log.py -q
python examples/adapter_contract_demo.py --fixture tests/fixtures/pi_hub --output /tmp/pix-consumer-new
python examples/chat_handover_demo.py --output /tmp/pix-chat-new
python tools/validate_usage_wheel.py --wheel /absolute/path/pix-0.5.0-py3-none-any.whl --output /tmp/pix-wheel-new --pix-commit FULL_VERIFIED_SHA
```

Install the pinned wheel first; the last command requires pip in its invoking
environment and constructs a clean temporary runtime containing only PIX and
platform-required dependencies. CI runs it on Linux, Windows and macOS. Schumpeter
must separately run the fixture in its own consuming environment before declaring
G1 integration complete. The artifact/verification labels above are synthetic
process facts, not hardcoded organization policy.
