# Neutral PI Hub consumer fixture

These synthetic records represent one task, two actors, one artifact and one
message. They contain no WMC collector, runtime hook, organization policy or
private transcript. The record format is local to the example, not a new public
PIX import schema.

- `normalized.json`: five exact, timezone-aware observations with explicit IDs,
  qualified E2O links and one artifact→task O2O link.
- `mapping.json`: the example's field selection, namespace and exact-time
  declaration. Its versioned hash uses the example's sorted, indented UTF-8 JSON
  encoding; it is not interchangeable with chat/table mapping hashes.
- `expected.json`: independently counted facts and hand-calculated durations.
  The runner compares these values and never updates them from its own output.

Task order is `started → artifact_written → verification_executed → sent → received`.
The four gaps are 60, 60, 60 and 30 seconds. Exactly one send/receive pair shares
`message:1`, so A→B has a 30-second latency and fulfills the 60-second response
window. Artifact creation precedes the verification event. This says nothing
about whether the verification succeeded or the task may be approved.

There are 5 events, 5 objects, 14 qualified E2O links and 1 O2O link. Selecting
only task objects gives one execution, one exact variant of frequency 1 and four
task DFG edges. The artifact O2O relation is preserved in I/O but does not produce
a DFG edge or execution connectivity.

## Reproduce

From the repository after installing this PIX checkout:

```bash
python examples/adapter_contract_demo.py --fixture tests/fixtures/pi_hub --output /tmp/pix-consumer-new
python -m pytest tests/test_pi_hub_consumer.py -q
```

Use a new output directory for each run. For installed-only verification, copy
this directory and `examples/adapter_contract_demo.py` outside the checkout,
then use that environment's `python -I` with explicit absolute paths. The
repository's `tools/validate_usage_wheel.py` automates this and also runs the
existing chat demo in the same core-only environment. `--pix-commit` and `--wheel`
record caller-declared build provenance; they do not authenticate the source.

The bundle contains the original input/mapping/expected files, JSON/XML/SQLite
OCEL snapshots, eight native analysis result documents, and `run-record.json`.
The latter is an example's execution record, not a new PIX or Schumpeter public
contract. Each result includes its native spec, operator, status and diagnostics;
the execution record links file hashes and all parent artifacts, including the
DFG parent of OCDFG. `source_digest` uses `CanonicalDigest.identifier`, not its
Python repr. Canonical equality does not require equal JSON/XML/SQLite file hashes.
`reference_schema=not_run` remains explicit: PIX round-trip validation is not
independent OCEL reference-schema certification.

## Acceptance coverage

| Plan cases | Executable evidence |
| --- | --- |
| F01/F02/F09 exact pipeline, all formats, IDs, provenance, parent closure, repeatability | `tests/test_pi_hub_consumer.py`; installed adapter example |
| F02 malformed references, duplicate IDs, missing/naive times | Consumer tests; `tests/ocel` covers I/O-specific behavior |
| F03/F04 time buckets, ID renaming, ambiguous/definite deadlines, external anchors, unknown upper, open/closed | Consumer tests and `tests/compute/test_time_precision.py` |
| F05 unsupported order semantics | Consumer tests; sequential operator refusals in `test_time_precision.py` |
| F06/F07 ID-based handovers, missing endpoints, repeated observations, changing groups | Consumer tests; fan-out, A→B/A→C/B→C, conflict, stable groups and limits in `tests/compute/test_handover.py` |
| F08 chat mapping identity, privacy defaults, matching rules, drops/defects | `tests/tabular/test_chat_log.py`; consumer tests add empty/dropped lineage and missing explicit carrier IDs |
| F09 codec compatibility and tamper rejection | `tests/test_results.py`, legacy fixture checks in `test_time_precision.py` |
| F10 standalone wheel | `tools/validate_usage_wheel.py` runs existing wheel checks and both copied examples; the report separately records the installed-wheel consumer pytest run |

The exact fixture does not establish support for uncertain sequential discovery.
The consumer tests construct uncertainty counterexamples through the same public
builder/API. No synthetic microsecond ordering is introduced. A completely
unanchored time fails explicitly. Original nulls, held/excluded events and runtime
coverage belong in the producer's source ledger. Do not merge unknown task IDs
into a real shared `UNKNOWN` object or present a selected snapshot as a complete
runtime history.
