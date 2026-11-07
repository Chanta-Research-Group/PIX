# Two-organization mapping fixture — 2026-11-07

## Scope and implementation

PIX owner added a synthetic collaboration mapping example, fixture and developer
tests on `work/pix-owner-intake-20261107`, based on
`6e9af5ee1b670de39a87be406518fea49dffdfec`. No engine, package metadata, consumer
pin or other repository was changed. The original PIX checkout remains at
`a0688f34e557c885c145051485072fd0623f263f` with its existing untracked ZIP.

The [fixture contract](../../tests/fixtures/collaboration_handover/README.md)
records exact local and proposed remote roles. The
[executable example](../../examples/collaboration_handover_demo.py) writes native
results through existing public codecs. The
[tests](../../tests/test_collaboration_handover_consumer.py) check semantic
invariants and deliberate failures rather than accepting generated snapshots
as the oracle. The [source manifest](evidence/collaboration-handover-20261107/source-manifest.json)
binds changed files and directly inspected producer material.

## Owner coordination and facts

Schumpeter owner identified PR8
`237417a5e5742888f565b30581387c7a2833a7f3`, local `collaboration.py` and
`collaboration_cli.py`. Those sources were read. Existing local message posts
and receipts use a message carrier, organization sender/recipient qualifiers
and explicit microsecond precision. Artifact submission/review uses exact byte
digests; one review carries both artifact revisions plus criterion/acceptance
references. The semantic fixture does not claim to capture the actual exporter
or reproduce its source namespace/native ID encoding. Consumer projection
through this fixture is still required.

Pida owner supplied its new envelope/receipt types and exact golden wire file,
then froze them in local commit `50d1ed49294cb8acfabb00badd72da6877e22c30`.
The golden file was copied without rewriting and its canonical payload digest
checked independently. Pida owner-reported focused persistence tests and
unresolved full-suite failures are separate from this PIX execution. No live
receipt, sender dispatch or runtime input consumption was observed here.

Coordination corrected the initial job-ID carrier proposal: the external key is
`(producer_id, request_id, recipient.organization_id)` **inside authenticated
owner scope**. The example's native carrier ID includes that owner scope as its
first tuple element. Missing scope fails; identical external keys under different
owners produce disjoint carriers. A production host must supply authenticated
scope, not trust a sender assertion. `job_id` remains the receipt's exact native
execution mapping. Different payload or receipt/job binding under one carrier
fails mapping.

The already adopted Pida `sequential-prefix/1` and `object-terminal/1` profiles
and their exact engine pins remain unchanged. This fixture does not reimplement
them or infer that a receipt supplies their case ordering evidence.

## New executable evidence

Final developer run: Windows, uv 0.11.29 selecting Python 3.13.14:

```text
uv run --no-project --with pytest --with tzdata python -m pytest -q tests/test_collaboration_handover_consumer.py tests/test_current_cut_consumer.py tests/test_pi_hub_consumer.py tests/compute/test_handover.py
82 passed in 3.41s
exit_code: 0
```

This consists of 21 new fixture tests plus the 61 existing targeted checks.
[Final output](evidence/collaboration-handover-20261107/focused-tests.txt) is
captured directly from the command. Ruff formatting and lint passed for both
new Python files. Engine/package diff against HEAD is empty.

Final native artifacts are under
[native-scoped/run-record.json](evidence/collaboration-handover-20261107/native-scoped/run-record.json).
The record includes source hashes, canonical OCEL digests, seven result
computation identities and hashes for all copied inputs/native outputs. Command:

```text
uv run --no-project --with tzdata python -c "import sys;sys.path.insert(0,'src');from examples.collaboration_handover_demo import run;r=run('tests/fixtures/collaboration_handover','docs/reports/evidence/collaboration-handover-20261107/native-scoped');print('Published',len(r['results']),'native results');print(sys.version)"
```

Use a fresh output directory when rerunning. Preserved earlier output under
`native/` and `focused-tests-pre-owner-scope.txt` predates the explicit owner
namespace and is **superseded**, not final acceptance evidence. An attempted
cleanup was blocked by tool policy; the final run safely used a new directory.
The initial new example also exposed a JSON serialization mistake in its own
run record (`CanonicalDigest` needed dataclass serialization); it was fixed
without changing PIX operators.

The initial readiness report's interpreter label was also corrected visibly:
bare Python 3.11.9 had been mistaken for uv's selected interpreter. See the
[correction record](evidence/owner-readiness-20261107/interpreter-correction.txt).
No Python 3.11 acceptance is inferred.

The actual checks establish these bounded facts:

- Late receive evidence joins its exact carrier while preserving negative
  latency/clock conflict; missing counterparts remain unmatched.
- Same timestamps, payload or local request label do not connect different
  producers, requests, recipients or authenticated owner scopes.
- Arrival array order and unrelated runtime/acceptance observations do not
  change handover results. No response, input inclusion or acceptance is inferred
  from enqueue.
- Source positions, when present, remain source-local. Missing positions stay
  absent. A separate explicitly sequenced synthetic case journal drives the
  online profile; a gap or receipt-arrival sequence basis is rejected.
- Existing joint alignment consumes shared verification once with two exact
  revisions; independent reads gain no edge. Open online cost stays partial and
  unresolved; terminal object completion cost is not a live-cut violation count.
- Local submit/review keeps exact byte digests and one shared review event;
  a changed artifact payload with an unchanged revision is rejected by the
  fixture's integrity check.

## Remaining acceptance and falsification

Independent review, actual Schumpeter production projection, desktop GUI,
installed-wheel and Linux acceptance were **NOT_RUN** in this slice. Pida's
actual receipt currently lacks a case source sequence; this is retained as a
coverage limit. Actual remote dispatch evidence and authenticated owner mapping
must be provided by their owners. Neutral PIX computation does not establish
grants, provenance authenticity, task acceptance or organizational improvement;
improvement is **알 수 없음**.

The next executable consumer unit is to feed actual Schumpeter projection into
this oracle, preserving source namespaces and the distinct handover spec/cache
identity. The synthetic mapping alone cannot close that gate. Pida/Schumpeter
must bind actual receipt/dispatch bytes before making a remote delivery claim.
Existing profile paths can continue while missing evidence is supplied; no
engine work is justified by the tested slice.

Validity is limited to the source hashes and selected profiles above. Withdraw
the mapping recommendation if a producer cannot establish the carrier/owner
binding, the native result contradicts the independent oracle, independent reads
gain causal edges, shared events are duplicated, or consumer serialization
erases partial/unknown/clock-conflict limits. Refresh after source, schema,
membership, model or policy changes. A demand for arbitrary-DAG or live object
current-cut alignment requires a separate contract and independent oracle.

Conclusion: **PASS for this bounded fixture implementation and developer
verification**; independent review and consumer desktop integration remain open.
