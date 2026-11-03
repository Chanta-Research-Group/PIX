# Current-cut profile comparison fixture

Synthetic, domain-neutral public-API acceptance for
[CR-PIDA-PIX-2026-11-03](../../../docs/change_requests/CR-PIDA-PIX-2026-11-03-RESPONSE.md).
No Pida, Persona, Schumpeter, account, token or network is required to run it.

```sh
python -m pip install -e '.[dev]'
python examples/current_cut_demo.py --fixture tests/fixtures/current_cut --output /tmp/pix-current-cut-new
python -m pytest -q tests/test_current_cut_consumer.py
```

Choose a new output directory; existing results are not overwritten. To check
an installed wheel, copy this script and `input.json` / `expected.json` to an
external directory, then run its interpreter with `-I`. The repository's
`tools/validate_usage_wheel.py` does this in a core-runtime-only environment.

| Input | Independent expected meaning |
| --- | --- |
| Explicit single-word DFG and Petri net in the example | `request → edit → test → deliver` is their only accepted word. Closing after two observations requires two model moves; an open prefix has a zero-cost executable witness. |
| `input.json` | Two exact artifact revision IDs, a common actor, shared start/verify and two independent reads. Exact timezone-aware points; no inferred order between reads. |
| `expected.json` | Hand-calculated costs/statuses/termination properties, checked before artifact publication. Not learned from a generated result snapshot. |
| `reference/` | Executed native results, checkpoint, model and OCEL artifacts, plus SHA-256 index and parent-artifact links. Generated evidence, not the correctness oracle. |

The example produces 18 native result documents (including three trace parents
and a checkpoint), two model documents, three OCEL snapshots, source/expected
inputs and `run-record.json`. `online_checkpoint.result.json` can be read with
`pix.results.read_result` and passed to `OnlineAlignmentStream.resume`. Appending
the remaining two events and the explicit close marker produces exactly the
same native bytes as uninterrupted processing.

The native result codec binds operator/spec/source and model identity as
appropriate; the run record additionally hashes actual artifact bytes. It is
an example index, not a new public result contract. Git source pin, wheel hash
and environment evidence are recorded in the validation report. `0.5.0` alone
does not distinguish source builds, and document hashes are not signatures.

The online result remains `partial` even for this exact finite example. Joint
object alignment requires final completion. The binding-prefix context metric
excludes the final observed downset. These three facts are acceptance checks,
not warnings to be removed. See the [matrix](../../../docs/user-guide/CURRENT_CUT_PROFILES.md)
for unsupported time/order/model conversions and host-owned scope/revision rules.

To deliberately regenerate reference bytes after reviewing a change, run into
a new directory and compare all artifacts before replacing the tracked fixture.
Tests also verify the tracked reference bytes against the public calculation.

The fixture JSON paths are pinned to LF through Git attributes, including on
Windows checkouts with `core.autocrlf=true`. This preserves the native byte
hashes; it does not normalize or change existing PIX engine source files.
