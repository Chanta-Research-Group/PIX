# PIX current-cut CR validation — 2026-11-03

PIX completed the owner-side capability selection and reusable verification for
[CR-PIDA-PIX-2026-11-03](../change_requests/CR-PIDA-PIX-2026-11-03-RESPONSE.md).
The existing engine is sufficient for a separate approximate sequential online
profile and a completed joint-object profile. Neither is an exact current-cut
replacement for Pida's arbitrary accepting DFG.

## Repository and delivery scope

| Item | Verified state |
| --- | --- |
| PIX main | `48fe7eb67388cda1144c5bba93adbfe00933ab1c` |
| Previous readiness work | Draft PR #13, unmerged, `3205d832d5dcdc6901f916b35496a0c60b657e7a` |
| Work branch | `work-pix-current-cut-20261103`, based on PR #13 |
| Engine/package | `0.5.0`; all 240 Python files under `src/pix` and `pyproject.toml` unchanged |
| Engine code SHA-256 | `b4fef3bce21c49dd4ab700b6188bdef16f9813810718932b23029522609c7510` |
| Requester inspected | `riesling-29/pida@bbc28a39495b0c5d1b5f471ba11927e9ad64b46f`, CR and unmodified worker/check |

The source hash uses the requester's compact JSON array of sorted
`[src/pix/path.py, sha256(raw bytes)]` pairs, preserving original line endings.
Keep Pida's existing exact engine pin `3205d832...`: its worker allowlists both
commit and digest. This patch is a new **fixture/documentation delivery**, not
permission to bypass that consumer check or install an unrelated index package.

Changes: `examples/current_cut_demo.py`; 25 consumer tests; hand-derived input
and expectations plus 18 native result/checkpoint fixtures; the profile matrix
and owner response; README entry; installed-wheel checker adds the copied
example. PIX remains usable independently, including standalone chat import.
No other app source, runtime hook, deployment, identity or policy was changed.

## Validation actually executed

| Check | Result |
| --- | --- |
| Existing focused baseline: online/object alignment + PI Hub consumer | 90 passed, 15 subtests passed |
| Full Linux Python 3.12.14 suite, pytest 9.2.0, import extras installed | **10,727 passed, 42 skipped, 1,169 subtests passed** in 93.75 s |
| New current-cut tests within that suite | **25 passed** |
| Changed Python files Ruff / diff whitespace | passed |
| Installed wheel outside checkout, `-I`, core dependencies only | mining + visualization checks and chat + PI Hub + current-cut examples passed |
| Current-cut native bytes from installed wheel | identical to checked-in reference; serialized checkpoint continuation equals uninterrupted result |
| Pida's unmodified Python worker/check against exact `3205d832...` source | **18 passed, 0 failed**; actual source computation on synthetic inputs |
| Remote multi-platform CI | pending on delivery commit; a separate evidence update records completion |

Local wheel SHA-256:
`fe77b74f47c25145e276bf5329aea165ede8c7ff9270c05838a4d52547885a45`
(2,102,672 bytes). The wheel was built from the local implementation tree before
delivery commit assignment; no source commit was claimed by the local wheel
checker. It installed only `pix==0.5.0` on Linux. Remote CI produces its own wheel
bytes. Machine-readable hashes, commands, JUnit summary and the 18 consumer
checks are in [the evidence record](evidence/current_cut_20261103.json).

The environment initially lacked pytest; an isolated editable dev/import
environment was installed before testing. A first demo invocation lacked the
required OCEL export format and was fixed before acceptance. A wheel attempt
without build isolation lacked setuptools; the normal isolated build succeeded.
These setup attempts are not counted as engine defects or hidden test passes.

A portability follow-up reproduced Git's `core.autocrlf=true` changing input
JSON bytes (9 CRLF endings). Scoped Git attributes now pin only current-cut
fixture JSON to LF. All 28 JSON files then matched byte-for-byte in a simulated
Windows checkout, and the 25 consumer tests passed again. Engine source endings
are untouched. The complete suite above predates this attributes-only behavior
change; the remote CI revision is recorded separately.

## What these results establish

- The same two-event prefix has terminal DFG cost 2 and online prefix witness
  cost 0; explicit close restores completion cost. Online remains `partial`.
- Independent artifact reads stay incomparable when IDs and global timestamps
  change. Joint verification retains both revision IDs and is consumed once.
- Same-object ties remain unavailable; limited searches preserve unknown cost.
- Duplicate delivery, correction conflict, gaps, capacity, checkpoint identity,
  new generation, omitted witness history and resumed bytes have explicit checks.
- Object-type selection leaves unrelated events in whole_log; scope filtering
  must precede the call. The object-context metric excludes the last observed
  downset and does not decide current-cut completion.
- All native parent IDs resolve where the operator supplies parents; model and
  input artifacts use existing codecs. No new parallel result schema was added.

## Remaining work and unsupported paths

Pida must select a separately versioned model/adapter profile and implement its
scope, cut revision, generation, policy/adoption and stale-result handling. The
25 PIX tests and 18 existing batch checks are **not** a live integration of the
new profile. Actual Pida online/object worker integration, LLM behavior, Persona
provider, production deployment and sustained outcome improvement are NOT_RUN.
No independent reviewer acceptance is claimed.

Exact optimal live-prefix cost for the existing arbitrary DFG, arbitrary
explicit-DAG input, same-object concurrent/uncertain-time object ordering, and
incremental object current-cut alignment remain unsupported by this selection.
The [matrix](../user-guide/CURRENT_CUT_PROFILES.md) explains the required model,
metric and termination distinctions. No generic engine defect was reproduced
within the selected supported inputs; new algorithms are not added speculatively.
