# Participant binding lineage correction — 2026-11-07

## Finding and resolution

Independent reviewer `pix_mapping_review` reproduced a material omission in
`bb67602ff60cb7927ad8419a9fd4752baccddd6c`: modifying a participant's `host_id`,
`org_session_id`, `agent_id` or `binding_revision` under the same participant ID
left native result bytes, source digest and computation ID unchanged. The
fixture validated these fields but only retained `organization_id` in OCEL.
There was no external immutable-ID enforcement to justify that equivalence.
The [original probe](evidence/participant-lineage-fix-20261107/original-review-probe.json)
is retained as evidence of the defect, not a passing result.

The mapping now stores all five fields as explicit string attributes on each
selected `collaboration_participant` object. Its object ID and qualified E2O
relations remain intact. PIX's existing canonical source digest includes those
attributes, so every material binding change invalidates the prior native
source/computation identity. No engine change was needed.

Four parameterized regression cases change the omitted fields independently
under a fixed participant ID. They verify retained attribute values, changed
source/computation identity and native bytes, and unchanged handover counts.
The serialized OCEL is also read back: every binding field remains present and
recomputation reproduces the saved native result.
Equal numerical answers do not establish equal source applicability. A changed
binding requires a newly identified analysis and consumer applicability checks;
this fixture cannot authenticate a binding or decide which actor is authorized.

The dynamic-membership regression initially selected the first attribute by
position, which stopped naming `organization_id` after canonical sorting of
the expanded attribute set. It now selects that attribute by name and still
checks that contradictory organization membership is rejected. The intermediate
failure is preserved in
[its log](evidence/participant-lineage-fix-20261107/test-attribute-position-failure.txt).
No failed assertion was removed or weakened.

## Developer verification

Windows, uv-selected Python 3.13.14; same targeted test command:

```text
uv run --no-project --with pytest --with tzdata python -m pytest -q tests/test_collaboration_handover_consumer.py tests/test_current_cut_consumer.py tests/test_pi_hub_consumer.py tests/compute/test_handover.py
86 passed in 1.73s
exit_code: 0
```

See [captured output](evidence/participant-lineage-fix-20261107/focused-tests.txt),
[mutation probe](evidence/participant-lineage-fix-20261107/lineage-probe.json),
and [source manifest](evidence/participant-lineage-fix-20261107/source-manifest.json).
Ruff checks passed. `src/pix` and `pyproject.toml` remain unchanged against the
previous commit. Four added lineage cases bring the fixture suite to 25 cases;
the 61 existing targeted checks still pass.

Replacement final artifacts are at
[native/run-record.json](evidence/participant-lineage-fix-20261107/native/run-record.json),
with seven native results, exact input/source hashes and five OCEL snapshots.
Regenerate into a fresh output directory with:

```text
uv run --no-project --with tzdata python -c "import sys;sys.path.insert(0,'src');from examples.collaboration_handover_demo import run;r=run('tests/fixtures/collaboration_handover','/absolute/new-output');print('Published',len(r['results']),'native results')"
```

The older `collaboration-handover-20261107/native-scoped` artifacts and 82-test
record remain a historical snapshot, now superseded by this correction.
Earlier owner-scope artifacts remain historical too. None are relabelled as
having contained the missing binding fields.

## Acceptance boundary and falsification

The prior independent review's failure is resolved in implementation and direct
developer tests; independent recheck of the new commit is still pending at this
record's creation. Actual production Schumpeter projection, receipt-to-binding
authentication and desktop integration remain separate open gates.

Withdraw this fix's sufficiency if any declared material binding field changes
while native source identity remains equal, a full binding is lost in native
OCEL serialization, or a consumer still reuses old analysis across binding
changes without proving equivalence. Validity is limited to this fixture schema,
selected fields and recorded source hashes; new binding fields require explicit
retention or an evidenced equivalence rule. The fixed attribute assignment time
is the synthetic snapshot convention, not inferred temporal membership.

Conclusion: **PASS for the focused correction and developer verification**;
independent recheck and production consumer acceptance remain open.
