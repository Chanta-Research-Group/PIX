# PIX

PIX is an independent, deterministic Process Intelligence computation and
interpretation engine.

## Status

The current usage work adds grouped trace comparison and a frequency-ranked
[trace variant catalog](docs/user-guide/TRACE_VARIANT_CATALOG_GUIDE.md).

Conversation logs can be imported with declarative turn and activity rules, then
analyzed as qualified sender/receiver handovers. Declared timestamp precision
preserves uncertain ordering and duration bounds. See the
[chat, handover and time precision guide](docs/user-guide/CHAT_HANDOVER_AND_TIME_PRECISION.md).
Top 20% selects 20% of distinct variants by count, rounded up; case coverage is
reported separately. Multiple sequences can be inspected in one offline view.
See the [trace variant catalog guide](docs/user-guide/TRACE_VARIANT_CATALOG_GUIDE.md)
and [trace group comparison guide](docs/user-guide/TRACE_GROUP_COMPARISON_GUIDE.md)
for tested scope. Historical reports retain their original evidence.

The [adapter compatibility patch plan](docs/requirements/2026-10-25_PIX_ADAPTER_COMPATIBILITY_PATCH_PLAN.md)
preserves standalone chat import and analysis and defines how future downstream PI operation reports enter follow-up work. The
[downstream PI Hub readiness plan](docs/requirements/2026-10-25_SCHUMPETER_PI_HUB_INTEGRATION_READINESS_PLAN.md)
prioritizes verification of existing APIs, consumer documentation, and reusable fixtures.
Generic mapping provenance and explicit time-bound extensions are conditional on
demonstrated contract gaps. These plans do not record implementation or new test passes.

The [consumer API matrix](docs/user-guide/SCHUMPETER_PIX_CONSUMER_API_MATRIX.md)
and [neutral integration fixture](tests/fixtures/pi_hub/README.md) now provide a
public-API example covering OCEL round-trips, eight native result artifacts, and
complete parent-artifact links. Installed-wheel validation runs this example and
the existing standalone chat demo. This does not certify an external downstream deployment.
See the [readiness report](docs/reports/2026-10-25_SCHUMPETER_PIX_READINESS_REPORT.md)
for the tested commit, wheel identity, results, and remaining consumer acceptance.

The [current-cut capability matrix](docs/user-guide/CURRENT_CUT_PROFILES.md)
maps existing public operators and a [reproducible comparison fixture](tests/fixtures/current_cut/README.md)
for downstream consumers.
The example contrasts terminal DFG cost, approximate open-prefix bounds, and
joint object alignment; it preserves unknown and unsupported outcomes.
Installed-wheel validation also runs this example outside the checkout.

Current requirements and responsibility boundaries are recorded in the
[downstream integration user requirements](docs/requirements/2026-09-13_PIX_SCHUMPETER_USER_REQUIREMENTS.md)
and [residual design](docs/requirements/2026-09-18_PIX_RESIDUAL_DETAILED_DESIGN.md).
The [OCPM consumption contract](docs/specifications/PIX_OCPM_CONSUMPTION_CONTRACT.md) and
[input semantics audit](docs/reports/2026-10-06_PIX_OCPM_INPUT_AUDIT.md) record public
projection and visualization obligations. Early v0.1 scope documents are historical
baselines, not removal instructions for later discovery/conformance features.

The residual implementation adds XES/DFG and OCEL bundle exchange, explicit
object-to-case projection, contextual n-grams, business-calendar path timing,
POWL footprints and single-trace fit checks. See the
[API guide](docs/user-guide/RESIDUAL_CORE_GUIDE.md) and
[scope and validation record](docs/reports/2026-09-18_PIX_RESIDUAL_CORE_IMPLEMENTATION.md).
This is a subset of the agreed residual plan, not a declaration of full upstream parity.

PIX `0.5.0` adds native case-centric logs and explicit business-table mappings to
the immutable OCEL foundation. Import profiles cover OCEL 1 JSON/XML and classic
SQLite, OCEL 2 JSON/XML/SQLite, OCEL 2.1.0pre4 compact CSV and CSV/Parquet bundles,
XES/MXML, mapped CSV/TSV/XLSX and iterable records. Case logs preserve source order,
empty traces and nested XES metadata; their explicit trace bridge feeds native
discovery and classical conformance. Verified atomic
exports (including JSON/XML gzip), object traces, DFG/OCDFG, observed temporal
measures, explicit execution extraction, and bounded exact incidence variants.
Native model functionality includes explicit log-based IM and conservative cut
profiles, process-tree conversion, observational OCPN discovery with a checked
accepting witness, Petri net/OCPN firing and bounded binding enumeration, classical
and joint object-centric alignment, token replay, prefix precision, object-context
fitness/precision and declarative rules. Results and models have separate versioned,
evidence-bearing JSON formats. The SVG viewer uses bundled Graphviz WebAssembly
for offline graph layout by default.

The unreleased native mining extension separates `pix.case_centric` and
`pix.object_centric`. It adds named discovery, conformance, performance, feature,
rule, model conversion, simulation and streaming profiles, including IMf/IMd
and normalized classical fitness. Existing `pix.inductive_cut.v1` and `pix.im.v1`
contracts remain distinct. See the [native mining guide](docs/user-guide/NATIVE_MINING_GUIDE.md),
[implementation scope](docs/requirements/2026-09-15_PIX_NATIVE_MINING_UNION.md)
and [validation record](docs/version/2026-09-15_NATIVE_MINING_VALIDATION.md).
The implementation registry distinguishes supported definitions, partial variants
and unverified optional runtime paths; it does not claim complete upstream parity.

The subsequent model/W4 implementation adds explicit PNML/PTML/BPMN exchange
profiles, model decomposition and coverability, observation-safe feature datasets,
held-out learning evaluation, resource and timed simulation, revisable streams,
and bounded action planning. The [implementation report](docs/reports/2026-09-17_MODELS_AND_W4_IMPLEMENTATION_REPORT.md)
explains domain examples, validation evidence and remaining limits;
the [model/W4 guide](docs/user-guide/MODELS_AND_W4_GUIDE.md) links the public APIs.

OCPN discovery's observed-log acceptance witness does not certify joint soundness
or normative cardinalities. Joint alignment consumes shared events once and
preserves per-object partial orders. Precision and context have named population
and termination definitions, and open observations retain pending rules. Search
limits and zero denominators are explicit. PM4Py and OCPA remain source references
and are not PIX runtime dependencies.

The [visualization guide](docs/user-guide/VISUALIZATION_GUIDE.md) covers
`build_visualization`, model annotations, footprint comparisons, variant-duration
views and object-centric variant chevrons. PIX owns the domain adapters, SVG and
interactions; **Graphviz is the default graph layout engine for both new and legacy
viewer documents**. Graphviz 16.0.0 is bundled through `@viz-js/viz` 3.30.0, including
its WebAssembly, so exported HTML needs no CDN, `dot` installation or Python
`graphviz` package. Native layout is an explicit experimental option for new
documents, and ELK is an explicit option for legacy documents; neither is a silent
fallback. Chevron views default to neutral horizontal presentation, with explicit
vertical/auto orientation and the previous colored `classic` style available.
Chevron lanes use domain-specific precedence slots rather than graph
layout or elapsed time. See the
[2026-09-16 decision and acceptance requirements](docs/requirements/2026-09-16_GRAPHVIZ_AND_OC_VARIANT_VISUALIZATION.md).
The
[visualization scope](docs/requirements/2026-09-15_PIX_VISUALIZATION_UNION.md)
records supported source semantics and remaining reference variants. See the
[visualization validation record](docs/version/2026-09-15_NATIVE_VISUALIZATION_VALIDATION.md)
for the earlier 2026-09-15 baseline; those counts do not validate the subsequent
Graphviz and chevron changes.

The [local artifact guide](docs/user-guide/ARTIFACTS_GUIDE.md) defines naming and
preservation rules for generated previews and validation records. In a workspace
with local artifacts, open `.artifacts/index.html` to browse the visual catalog.

## Implemented import flow

```text
OCEL 1 / OCEL 2 / OCEL 2.1 profile --> immutable OCEL --> native OC analysis
XES / MXML -------------------------> native CaseLog --> case traces
Mapped CSV / TSV / XLSX / records --> either model        |
                                                         v
                                     native discovery / classical conformance

Every path retains source evidence, diagnostics and disclosed transformations.
CaseLog -> OCEL is an explicit, checked projection with native provenance.
Validated OCEL -> Canonical V1 bytes -> SHA-256 digest.
```

The canonical format is an internal identity representation, not an OCEL 2.0
file format. Its byte-level rules are documented in
[`docs/specifications/PIX_OCEL_CANONICAL_V1.md`](docs/specifications/PIX_OCEL_CANONICAL_V1.md).

Start with the [complete import guide](docs/design/2026-09-12-import-v050.md)
for format profiles, native case semantics, mappings and OCEL 2.1 boundaries.
The
[OCEL reading user guide](docs/user-guide/OCEL_READING_GUIDE.md) covers OCEL 2.0
inputs, timestamp behavior, object inspection, and failure diagnostics.
For the implemented analysis pipeline, output contracts, and reproducible viewer,
see the [native analysis guide](docs/user-guide/NATIVE_ANALYSIS_GUIDE.md),
[model evaluation structure](docs/user-guide/NATIVE_MODEL_EVALUATION_GUIDE.md) and
[model evaluation evidence](docs/version/v0.4.0_MODEL_EVALUATION_IMPLEMENTATION.md).

## Unified log API

```python
from pix import import_log, read_log
from pix.api import CaseTableMapping, case_traces

case_log = read_log("example.xes.gz")
traces = case_traces(case_log)  # source order; missing times stay unknown
result = import_log(
    "business.csv",
    mapping=CaseTableMapping(case_id="case", activity="task"),
)
print(result.describe())
```

Core formats use the standard library. XLSX requires `pip install "pix[excel]"`;
Parquet bundles require `pip install "pix[parquet]"`; `pix[imports]` installs both.
OCEL 2.1 support targets the pinned **2.1.0pre4** PDF, not a final-standard
certification. Generic database connections, generic Parquet tables, legacy
`.xls` and MXML export remain outside this profile. XES export was outside the
initial import release; the subsequent residual extension implements native
XES/gzip/bytes export as described in the residual guide.

## Public OCEL API

The `pix.ocel` namespace exports convenient readers, diagnostic import results,
the model, builder, validator, and canonical identity functions:

```python
from pix.ocel import import_ocel, read_ocel

ocel = read_ocel("example.jsonocel")
print(ocel.summary())
print(ocel.describe())
print(ocel.timezone_type)  # UTC
print(ocel.timezone_info.to_dict())
print(ocel.warnings)
print(ocel.events_by_type("create order"))

# Use import_ocel when failure evidence is needed instead of an exception.
result = import_ocel("example.sqlite")
print(result.summary())
print(result.describe())
```

Invalid semantic candidates do not receive canonical bytes or a digest. Import
results retain structured issues, transformations, source hash and size, and,
when mapping completed, the invalid candidate for diagnostics. `read_ocel()`
raises `OCELImportError`; its `result` attribute exposes the same evidence.

The reader represents canonical timestamps in UTC. Numeric-offset timestamps,
including supported legacy forms, retain their instants. When a timestamp has
no timezone, PIX assumes UTC, emits one aggregated
`TimezoneAssumptionWarning`, and retains the count in `ocel.timezone_info` and
`ocel.warnings`. Import provenance does not affect OCEL equality or its
canonical digest.

## MCP server and agent skill

PIX can run as a [Model Context Protocol](https://modelcontextprotocol.io)
server, so AI agents call PIX operators as tools instead of writing analysis
code. The SDK is optional:

```bash
python -m pip install -e ".[mcp]"
pix-mcp --root /path/to/event-logs
```

The server speaks MCP over stdio and reads or writes files only below the
`--root` directories (repeatable; `PIX_MCP_ROOTS` is the environment
equivalent; the default is the working directory). Register it in a client:

```bash
claude mcp add pix -- pix-mcp --root /path/to/event-logs
```

```json
{
  "mcpServers": {
    "pix": {"command": "pix-mcp", "args": ["--root", "/path/to/event-logs"]}
  }
}
```

The JSON form fits Cursor (`.cursor/mcp.json`), Claude Desktop and other
clients. Tools:

| Tool | PIX operator |
| --- | --- |
| `pix_capabilities` | adapter limits, formats and operator map |
| `pix_open_log` | `pix.io.import_log` (tables need explicit case and activity columns) |
| `pix_project_cases` | OCEL object-to-case projection |
| `pix_inspect` | counts, activities, start/end activities, time range |
| `pix_filter` | `filter_case_log`; includes `start_and_end` with `start_activities` / `end_activities`; chain calls to combine |
| `pix_variants` | `catalog_trace_variants` |
| `pix_discover_dfg` / `pix_discover_ocdfg` | case DFG / object-centric DFG |
| `pix_case_performance` | `measure_case_performance` |
| `pix_discover_process_model` | Inductive Miner (`im`, `imf`, `imd`) |
| `pix_load_model` | PNML, PTML, BPMN, PIX model JSON |
| `pix_conformance` | alignment fitness with deviations, or token-replay fitness |
| `pix_export` | XES, OCEL JSON/XML/SQLite, PNML/PTML/JSON models |
| `pix_list_handles` / `pix_release` | session handle table |

Logs and models are kept in the server process and passed between tools as
handles (`log-1`, `model-2`). Results are JSON with a `status` of `computed`,
`partial`, `invalid_input`, `unavailable` or `error`, plus PIX's issues and
computation IDs. Lists are capped by `max_items` and responses by
`--max-response-bytes`. The adapter only calls PIX operators; it does not
approximate an operation PIX lacks. The tool logic in `pix.mcp.tools` has no
SDK dependency and can be embedded directly.

[`skills/pix/SKILL.md`](skills/pix/SKILL.md) is an Agent Skill that tells an
agent when to use these tools, in which order, and how to read the results.
Copy the `skills/pix` folder into your client's skills directory.

## Dependency boundary

```text
Downstream consumers -> PIX
PIX -X-> downstream consumer packages
```

PIX must not import downstream consumer packages. It also has no runtime dependency on PM4Py,
OCPA, or pandas. Python `>=3.10` is required.

## License

PIX is licensed under the [Apache License, Version 2.0](LICENSE).

Bundled third-party assets in `src/pix/viewer/assets/vendor/` include
[ELK](src/pix/viewer/assets/vendor/ELK-LICENSE.md) and
[Graphviz-related](src/pix/viewer/assets/vendor/GRAPHVIZ-LICENSE.txt) components
under the Eclipse Public License 2.0, plus other vendor notices shipped with
those files. Their license texts are kept alongside the bundles.

## Repository structure

```text
docs/                  Architecture, specifications, version baselines, and references
docs/user-guide/       Task-oriented public API user guides
src/pix/ocel/          OCEL readers, writers, model, validation, canonical identity
src/pix/event_log/     Native case logs, XES/MXML readers and explicit projections
src/pix/tabular/       Explicit case/object mappings over business tables
src/pix/contracts/     Immutable analysis and model contracts
src/pix/compute/       Native analysis and model execution
src/pix/case_centric/  Case-centric discovery, conformance and analysis families
src/pix/object_centric/ Object-centric models, execution and analysis families
src/pix/viewer/        Offline SVG/chevrons, default Graphviz and explicit layout alternatives
src/pix/mcp/           Optional MCP server (`pix-mcp`) over the public operators
skills/pix/            Agent Skill for using the MCP server
examples/             Executable end-to-end native pipeline
tests/                Stage-specific, integration, and optional browser tests
tests/fixtures/        Local sample event logs; excluded from release commits by default
```

## Development

Install the package with development tools:

```bash
python -m pip install -e ".[dev]"
```

Run the checks:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m ruff check .
python -m ruff format --check .
```

The optional browser suite uses `pip install -e ".[dev,browser]"`,
`python -m playwright install chromium`, and `PIX_RUN_BROWSER=1` before running
`python -m pytest tests/browser -q`. JavaScript geometry tests run with
`node --test tests/viewer/test_layout.cjs` (see the viewer README for all tests).

On PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m pytest -q -p no:cacheprovider
Remove-Item Env:PYTHONDONTWRITEBYTECODE
```

Passing the current checks establishes consistency for the implemented
contracts, format adapters, and tested canonical vectors. It does not establish
compatibility with every producer-specific extension, scalability at arbitrary
data volumes, process-intelligence correctness, or production readiness.
