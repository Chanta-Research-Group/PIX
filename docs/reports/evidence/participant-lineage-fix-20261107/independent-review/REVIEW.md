# Independent PIX mapping review

Reviewer: `/root/pix_mapping_review`, separate context, same Codex model family.
Author commit: `bb67602ff60cb7927ad8419a9fd4752baccddd6c`.
Base: `6e9af5ee1b670de39a87be406518fea49dffdfec`.
Review checkout: `D:/ChantaResearchGroup/PIX-mapping-review-20261107`.
No author source or engine files were edited by this reviewer.

## Confirmed finding at original commit

**P2 — full participant binding disappears from native source identity.**
`mapped_log` validates nonempty `host_id`, `org_session_id`, `agent_id`, and
`binding_revision`, but records only `organization_id` as a participant object
attribute. Its event observation digest includes the event row only, not the
participant snapshot. Replacing any of the four binding fields while retaining
the supplied participant ID produces byte-identical native results, including
the same source digest and computation ID. Thus the proposed mapping cannot
distinguish changed native execution attribution when used as a source/cache
identity oracle. This is a provenance omission in the synthetic fixture, not a
demonstrated live authorization bypass. Owner confirmed that there is no
external immutable-ID enforcement for this fixture and is correcting it.

Reproducer and results: `review_probe.py`, `review-probe.json`. The script uses
the public native computation API against the frozen checkout; it does not
change source files. It changes each binding field in a deep copy of fixture
input and compares native bytes/source/computation identities.

## Independent evidence before correction

Actual command in the frozen review checkout:

```text
uv run --no-project --with pytest --with tzdata python -m pytest -q tests/test_collaboration_handover_consumer.py tests/test_current_cut_consumer.py tests/test_pi_hub_consumer.py tests/compute/test_handover.py
82 passed in 2.44s
exit_code: 0
tool chunk: da9597
```

The separately executed probe reported Python 3.13.14. All 11 source manifest
hashes, 8 run-record source hashes, 16 artifact hashes, native-record hash and
test-log hash match. Freshly regenerated seven native results and full run
record match committed evidence. `src/pix` and `pyproject.toml` have no diff
from the base. Interpreter correction preserves the historical mislabel and
does not claim Python 3.11 testing.

Source inspection at Schumpeter PR8 `237417a5e5742888f565b30581387c7a2833a7f3`
confirms local sent/received message qualifiers, intended recipient versus
receipt distinction, exact artifact byte-digest revisions and one review event.
Pida `50d1ed49294cb8acfabb00badd72da6877e22c30` confirms owner-scoped
producer/request/recipient-organization dedup key and job-enqueued receipt
meaning. Fixture documents correctly distinguish synthetic observations from
actual exporter/dispatch bytes. Current-cut examples remain separate from the
remote receipt stream; no case sequence is inferred from receipt timestamps.

The supplied tests independently reproduce owner-scoped carrier separation,
payload/receipt conflicts, arrival-order invariance, unmatched and clock-conflict
retention, shared-event single consumption, partial prefix versus terminal
completion semantics, and native serialization roundtrip.

## Scope and withdrawal

Review remains open until the confirmed lineage omission is corrected and its
new source/artifact identity is rechecked. No deployed adapter, installed wheel,
Linux GUI, desktop acceptance, actual provider execution, or cross-family review
was performed. Conclusions apply only to inspected hashes and commits; source,
schema or authority changes require renewed review. Production projection and
authenticated binding remain explicit future consumer gates.

## Correction recheck

The above original-commit review state is superseded by this delta review.
Owner fixed the finding in `158e791dd601cf63ca02d3ebc824774dcfd86d3e`.
Independent review checkout:
`D:/ChantaResearchGroup/PIX-mapping-review-fix-20261107`.

The implementation now retains all five binding fields as declared OCEL
participant attributes. Four new regressions and the independent `fix_probe.py`
confirm that changing host, native organization session, agent or binding
revision under the same participant ID changes native source digest,
computation ID and result bytes, while handover counts can legitimately remain
equal. Serialized OCEL retains each field and reproduces the saved computation.
No engine change or weakening of the dynamic-membership check was found.

The same targeted test command at this exact commit returned:

```text
86 passed in 2.51s
exit_code: 0
tool chunk: 8c4e15
```

Independent fix probe: `fix_probe.py`, `fix-probe.json` (tool chunk `0115ce`).
All 12 final source hashes, 5 evidence hashes, 8 run source hashes and 16 native
artifact hashes match. Fresh regeneration of seven results and the entire native
run record matches the committed replacement. The original omission, old
artifacts and intermediate test failure are preserved and labelled superseded.

Final verdict: **PASS for the corrected synthetic fixture/oracle scope** at
`158e791dd601cf63ca02d3ebc824774dcfd86d3e`. No outstanding material finding in
that scope. Production projection, authentic receipt-to-binding correspondence,
actual runtime/desktop integration and other environments remain unaccepted.
This is separate-context same-family review. The verdict expires when the
reviewed source or relevant contract changes; a counterexample that retains
source identity across a declared material binding change reopens the finding.
