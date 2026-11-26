---
name: pix
description: Process mining on local event logs with the PIX MCP server. Use when the user asks about process flows, variants, bottlenecks, case durations, rework, conformance or fitness against a process model, or wants to filter, discover or export an XES, OCEL 2.0, CSV or XLSX event log.
---

# PIX process mining

PIX computes process-mining results deterministically from local event logs.
The `pix-mcp` server exposes PIX as MCP tools. Every number you report must
come from a PIX tool result.

## When to use

- The user has an event log (XES, MXML, OCEL 2.0 JSON/XML/SQLite, CSV, TSV,
  XLSX) and asks how the process runs, which paths are common, where time goes
  or how well it matches a model.
- The user wants a subset of cases (by start or end activity, variant, time
  window, attribute, duration, path) exported for another tool.
- The user has a PNML, PTML or BPMN model and asks about fitness or deviations.

Skip it for questions that need no event data, or for logs on a remote
service. Download the data to a local file first; PIX reads only local files.

## Set up the server

Install PIX with the MCP extra, from a clone of this repository:

```bash
python -m pip install -e ".[mcp]"
pix-mcp --version
```

or straight from Git:

```bash
python -m pip install "pix[mcp] @ git+https://github.com/Chanta-Research-Group/PIX"
```

`pix-mcp` speaks MCP over stdio. It may read and write files only below its
allowed roots: pass `--root DIR` (repeatable) or set `PIX_MCP_ROOTS`
(separated by `:` on Linux and macOS, `;` on Windows). Without either, the
root is the directory the client starts it in.

Claude Code:

```bash
claude mcp add pix -- pix-mcp --root /path/to/event-logs
```

Cursor (`.cursor/mcp.json` in the project, or `~/.cursor/mcp.json`), Claude
Desktop and most other MCP clients use the same shape:

```json
{
  "mcpServers": {
    "pix": {
      "command": "pix-mcp",
      "args": ["--root", "/path/to/event-logs"]
    }
  }
}
```

If `pix-mcp` is not on the client's `PATH`, give the absolute path of the
script inside the virtual environment, or use `"command": "python"` with
`"args": ["-m", "pix.mcp.server", "--root", "..."]`.

To install this skill, copy the `skills/pix` folder into your client's skills
directory, for example `~/.claude/skills/pix` or `.claude/skills/pix`.

## Workflow

1. `pix_open_log(path, ...)`. For CSV/TSV/XLSX pass `case_column` and
   `activity_column`, plus `timestamp_column` and `resource_column` when the
   table has them. PIX never guesses these columns: if the user did not name
   them, read the header and ask, or state your choice in the answer.
2. `pix_inspect(handle)`. Read the case and event counts, activities, start
   and end activities and the time range before analyzing anything.
3. OCEL only: `pix_discover_ocdfg(handle, object_types)` for the object-centric
   view, or `pix_project_cases(handle, object_type)` to get a case log for the
   case-centric tools below.
4. Narrow the log with `pix_filter`. Each call applies one predicate and
   returns a new handle; filter that handle again to combine predicates (AND).
   - Start with A and end with C: `kind="start_and_end",
     start_activities=["A"], end_activities=["C"]` (first and last activity
     must match; not the same as eventually-follows). Or chain
     `kind="start", activities=["A"]` then `kind="end", activities=["C"]`.
   - Complement: `positive=false`.
   - Time window: `kind="time"` with timezone-aware ISO times.
   - Top variants: `kind="variant_frequency", top_k=5`.
5. Describe the process:
   - `pix_variants` for the most frequent paths and their case shares.
   - `pix_discover_dfg` for activity transitions (`counting="cases"` to count
     each case once per transition).
   - `pix_case_performance` for case durations in seconds and the slowest cases.
     On large logs it can return `unavailable` with an `interval_limit` issue;
     call it again with a larger `max_interval_pairs` (for example 20000000)
     or filter the log first.
6. Compare with a model: `pix_discover_process_model` (Inductive Miner `im`,
   `imf` with `noise_threshold`, or `imd`) or `pix_load_model(path)`, then
   `pix_conformance(log_handle, model_handle, method="alignment")`.
7. `pix_export(handle, path)` writes a filtered log (XES), an OCEL log
   (json, xml, sqlite) or a model (pnml, ptml, json). Existing files stay
   unless you pass `overwrite=true`.

Call `pix_capabilities` when unsure what is supported, `pix_list_handles` to
recover handles, and `pix_release` to free large logs. Handles live in the
server process and disappear when it restarts.

## Reading results

- `status` is one of `computed`, `partial`, `invalid_input`, `unavailable`,
  `error`. Report `partial` and `unavailable` as they are. Do not estimate the
  missing part, and do not swap in another library to produce the number.
- `issues` explain limits and assumptions. A `source_sequence` issue means
  event order is the order in the file, which is not proof of timestamp or
  causal order.
- Fitness values are exact ratios (`numerator`, `denominator`, `value`). Quote
  the value and keep the counts when precision matters.
- In alignments, a log move is an event the model cannot follow; a model move
  is an activity the model requires but the case lacks. Cases with status
  `search_limit` were not fully aligned; raise `max_states` or filter first.
- A model discovered from a log fits that same log well by construction. To
  judge conformance, compare against a reference model or a model discovered
  from a different subset.
- `truncated: true` means a list was capped by `max_items`. The totals next to
  it (`variant_count`, `edge_count`, `cases`) still cover the whole log.
- Durations are seconds. Convert them for the user and keep the unit explicit.
- Say which handle and filters a number came from, so the user can reproduce it.
