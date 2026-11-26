"""``pix-mcp``: serve PIX tools over MCP stdio with the official Python SDK.

Install with ``pip install "pix[mcp]"``. The server reads and writes files only
below the allowed roots (``--root``, repeatable, or ``PIX_MCP_ROOTS`` separated
by the OS path separator; default: the working directory). Only the stdio
transport is offered, so file access stays with the local client process.
"""

import argparse
import inspect
import os
import sys
from typing import Annotated, Any

from pix import __version__
from pix.mcp.tools import (
    DEFAULT_MAX_ITEMS,
    DEFAULT_MAX_RESPONSE_BYTES,
    FILTER_KINDS,
    PixToolbox,
)

INSTRUCTIONS = """PIX computes process-mining results from local event logs.
Typical order: pix_open_log -> pix_inspect -> (pix_project_cases for OCEL)
-> pix_filter (repeat to combine predicates) -> pix_variants / pix_discover_dfg /
pix_case_performance -> pix_discover_process_model or pix_load_model ->
pix_conformance -> pix_export. Logs and models are passed between tools as
handles such as log-1 and model-2. Every result has a status: computed, partial,
invalid_input, unavailable or error. Report partial and unavailable results as
such; do not fill gaps with estimates. Event order is the source order in the
file unless the import says otherwise."""


def _sdk():
    try:
        from mcp.server.mcpserver import MCPServer as Server
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP as Server
        except ImportError as error:
            raise SystemExit(
                'pix-mcp needs the MCP Python SDK: pip install "pix[mcp]"'
            ) from error
    from mcp.types import ToolAnnotations
    from pydantic import Field

    return Server, ToolAnnotations, Field


def build_server(toolbox: PixToolbox):
    """Register every PixToolbox tool on an MCP server object and return it."""
    Server, ToolAnnotations, Field = _sdk()
    options = {"instructions": INSTRUCTIONS}
    if "version" in inspect.signature(Server.__init__).parameters:
        options["version"] = __version__
    server = Server("pix", **options)
    read = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
    session = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=False
    )
    write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=False,
    )

    Handle = Annotated[
        str, Field(description="handle returned by an earlier tool, e.g. log-1")
    ]
    MaxItems = Annotated[
        int | None,
        Field(description=f"cap on listed rows (default {toolbox.default_max_items})"),
    ]

    @server.tool(
        name="pix_capabilities",
        description="Describe this PIX server: version, allowed roots, limits, "
        "supported formats, filter kinds and the PIX operator behind each tool. "
        "Call first when unsure what PIX can compute.",
        annotations=read,
    )
    def pix_capabilities() -> dict[str, Any]:
        return toolbox.capabilities()

    @server.tool(
        name="pix_open_log",
        description="Import a local event log (XES, MXML, OCEL 2.0 JSON/XML/SQLite, "
        "or CSV/TSV/XLSX) and return a handle. Tables need case_column and "
        "activity_column; PIX never guesses them. Returns import evidence "
        "(format, SHA-256, transformations, issues).",
        annotations=session,
    )
    def pix_open_log(
        path: Annotated[str, Field(description="file path inside an allowed root")],
        format: Annotated[
            str | None, Field(description="parser override, e.g. xes, ocel20-json, csv")
        ] = None,
        case_column: Annotated[
            str | None, Field(description="table column holding the case ID")
        ] = None,
        activity_column: Annotated[
            str | None, Field(description="table column holding the activity")
        ] = None,
        timestamp_column: Annotated[
            str | None, Field(description="table column with timezone-aware ISO times")
        ] = None,
        resource_column: Annotated[
            str | None, Field(description="table column mapped to org:resource")
        ] = None,
        event_id_column: Annotated[
            str | None, Field(description="table column with source event IDs")
        ] = None,
        order: Annotated[
            str, Field(description="source (file order) or timestamp (stable sort)")
        ] = "source",
        reject_timezone_assumptions: Annotated[
            bool, Field(description="refuse OCEL times that PIX had to assume are UTC")
        ] = False,
        max_items: MaxItems = None,
    ) -> dict[str, Any]:
        return toolbox.open_log(
            path,
            format,
            case_column,
            activity_column,
            timestamp_column,
            resource_column,
            event_id_column,
            order,
            reject_timezone_assumptions,
            max_items,
        )

    @server.tool(
        name="pix_project_cases",
        description="Turn an OCEL handle into a case-log handle with one case per "
        "object of object_type. Needed before case-centric tools on OCEL data.",
        annotations=session,
    )
    def pix_project_cases(
        handle: Handle,
        object_type: Annotated[
            str, Field(description="OCEL object type to use as the case notion")
        ],
        tie_policy: Annotated[
            str,
            Field(
                description="reject (equal timestamps fail) or event_id (break ties by event ID)"
            ),
        ] = "reject",
    ) -> dict[str, Any]:
        return toolbox.project_cases(handle, object_type, tie_policy)

    @server.tool(
        name="pix_inspect",
        description="Summarize a handle. Case log: cases, events, activities, start "
        "and end activities, time range, attribute keys. OCEL: event and object "
        "types, relation counts, time range. Model: type and size.",
        annotations=read,
    )
    def pix_inspect(handle: Handle, max_items: MaxItems = None) -> dict[str, Any]:
        return toolbox.inspect(handle, max_items)

    @server.tool(
        name="pix_filter",
        description="Apply ONE PIX case filter to a case log and get a new handle. "
        "Combine predicates by filtering the returned handle again (AND), or use "
        "kind=start_and_end with start_activities and end_activities for cases whose "
        "first activity is in start_activities and last in end_activities. "
        "Example: A to C = kind=start_and_end start_activities=[A] end_activities=[C], "
        "or chain kind=start activities=[A] then kind=end activities=[C]. "
        "kind uses: activity/start/end/rework/different_resources -> activities; "
        "start_and_end -> start_activities and end_activities; "
        "directly_follows/eventually_follows/path_duration/four_eyes -> "
        "pattern of 2; sequence/prefix/suffix -> pattern; variants -> variants; "
        "length/duration(seconds)/rework -> minimum/maximum; variant_frequency -> "
        "top_k or cumulative_coverage or minimum/maximum share 0..1; time -> "
        "time_start/time_end (+time_mode contained|intersects|start|end); "
        "event_attribute/case_attribute/attribute_frequency -> attribute_*; "
        "case_limit -> top_k. positive=false keeps the complement. "
        "mode=events keeps matching events instead of whole cases (activity, "
        "event_attribute, attribute_frequency, time only).",
        annotations=session,
    )
    def pix_filter(
        handle: Handle,
        kind: Annotated[str, Field(description="one of: " + ", ".join(FILTER_KINDS))],
        activities: list[str] | None = None,
        start_activities: Annotated[
            list[str] | None,
            Field(description="for kind=start_and_end: allowed first activities"),
        ] = None,
        end_activities: Annotated[
            list[str] | None,
            Field(description="for kind=start_and_end: allowed last activities"),
        ] = None,
        pattern: list[str] | None = None,
        variants: Annotated[
            list[list[str]] | None,
            Field(description="complete activity sequences to keep"),
        ] = None,
        minimum: float | None = None,
        maximum: float | None = None,
        time_start: Annotated[
            str | None, Field(description="ISO 8601 with timezone")
        ] = None,
        time_end: Annotated[
            str | None, Field(description="ISO 8601 with timezone")
        ] = None,
        time_mode: str | None = None,
        mode: Annotated[
            str | None, Field(description="cases (default) or events")
        ] = None,
        quantifier: Annotated[
            str | None, Field(description="any (default) or all")
        ] = None,
        positive: bool = True,
        top_k: int | None = None,
        cumulative_coverage: float | None = None,
        attribute_key: str | None = None,
        attribute_operator: Annotated[
            str, Field(description="equals, numeric_range or present")
        ] = "equals",
        attribute_values: list[Any] | None = None,
        attribute_value_type: Annotated[
            str,
            Field(
                description="string, id, int, float, boolean, date or null; must match the recorded type"
            ),
        ] = "string",
        attribute_minimum: float | None = None,
        attribute_maximum: float | None = None,
        max_items: MaxItems = None,
    ) -> dict[str, Any]:
        return toolbox.filter(
            handle,
            kind,
            activities,
            start_activities,
            end_activities,
            pattern,
            variants,
            minimum,
            maximum,
            time_start,
            time_end,
            time_mode,
            mode,
            quantifier,
            positive,
            top_k,
            cumulative_coverage,
            attribute_key,
            attribute_operator,
            attribute_values,
            attribute_value_type,
            attribute_minimum,
            attribute_maximum,
            max_items,
        )

    @server.tool(
        name="pix_variants",
        description="List exact activity variants of a case log, most frequent "
        "first, with case counts, shares and an example case ID.",
        annotations=read,
    )
    def pix_variants(handle: Handle, max_items: MaxItems = None) -> dict[str, Any]:
        return toolbox.variants(handle, max_items)

    @server.tool(
        name="pix_discover_dfg",
        description="Directly-follows graph of a case log: activity counts, start "
        "and end activities, edges by frequency. counting=cases counts each "
        "case once per pair.",
        annotations=read,
    )
    def pix_discover_dfg(
        handle: Handle,
        counting: Annotated[
            str, Field(description="occurrences or cases")
        ] = "occurrences",
        max_items: MaxItems = None,
    ) -> dict[str, Any]:
        return toolbox.discover_dfg(handle, counting, max_items)

    @server.tool(
        name="pix_discover_ocdfg",
        description="Object-centric directly-follows graph of an OCEL handle, one "
        "graph per requested object type.",
        annotations=read,
    )
    def pix_discover_ocdfg(
        handle: Handle,
        object_types: Annotated[
            list[str], Field(description="OCEL object types to include")
        ],
        max_items: MaxItems = None,
    ) -> dict[str, Any]:
        return toolbox.discover_ocdfg(handle, object_types, max_items)

    @server.tool(
        name="pix_case_performance",
        description="Observed case durations in seconds (summary statistics), "
        "arrival and completion gaps, and the slowest cases. Needs timestamps.",
        annotations=read,
    )
    def pix_case_performance(
        handle: Handle,
        max_interval_pairs: Annotated[
            int,
            Field(
                description="budget for comparing case intervals (concurrency); "
                "raise it when the result is unavailable with interval_limit"
            ),
        ] = 1_000_000,
        max_items: MaxItems = None,
    ) -> dict[str, Any]:
        return toolbox.case_performance(handle, max_interval_pairs, max_items)

    @server.tool(
        name="pix_discover_process_model",
        description="Discover a process tree with PIX's Inductive Miner (im, imf "
        "with noise_threshold 0..1, or imd) and keep it as a model handle with "
        "its Petri net for pix_conformance.",
        annotations=session,
    )
    def pix_discover_process_model(
        handle: Handle,
        variant: Annotated[str, Field(description="im, imf or imd")] = "im",
        noise_threshold: Annotated[
            float, Field(description="only for imf, 0..1")
        ] = 0.0,
        max_items: MaxItems = None,
    ) -> dict[str, Any]:
        return toolbox.discover_process_model(
            handle, variant, noise_threshold, max_items
        )

    @server.tool(
        name="pix_load_model",
        description="Load a PNML, PTML, BPMN or PIX model JSON file as a model "
        "handle. BPMN is converted with PIX's own BPMN-to-Petri-net compiler; "
        "if that fails, conformance on it is unavailable.",
        annotations=session,
    )
    def pix_load_model(
        path: Annotated[str, Field(description="model file inside an allowed root")],
    ) -> dict[str, Any]:
        return toolbox.load_model(path)

    @server.tool(
        name="pix_conformance",
        description="Check how well a case log fits a model. method=alignment "
        "(optimal alignments; fitness plus log/model move counts per activity) or "
        "token (token-based replay fitness). Fitness ratios are exact "
        "numerator/denominator pairs. search_limit cases make the result partial.",
        annotations=read,
    )
    def pix_conformance(
        log_handle: Handle,
        model_handle: Handle,
        method: Annotated[str, Field(description="alignment or token")] = "alignment",
        max_states: Annotated[
            int, Field(description="alignment search bound per case")
        ] = 10_000,
        include_deviations: Annotated[
            bool, Field(description="also count log and model moves per activity")
        ] = True,
        max_items: MaxItems = None,
    ) -> dict[str, Any]:
        return toolbox.conformance(
            log_handle, model_handle, method, max_states, include_deviations, max_items
        )

    @server.tool(
        name="pix_export",
        description="Write a handle to a file inside an allowed root: case log as "
        "XES, OCEL as json/xml/sqlite, model as pnml/ptml/json. Existing files "
        "are kept unless overwrite=true; opened source files are never replaced.",
        annotations=write,
    )
    def pix_export(
        handle: Handle,
        path: Annotated[
            str, Field(description="destination file inside an allowed root")
        ],
        format: Annotated[
            str | None, Field(description="xes | json, xml, sqlite | pnml, ptml, json")
        ] = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        return toolbox.export(handle, path, format, overwrite)

    @server.tool(
        name="pix_list_handles",
        description="List the open log and model handles with their origin.",
        annotations=read,
    )
    def pix_list_handles() -> dict[str, Any]:
        return toolbox.list_handles()

    @server.tool(
        name="pix_release",
        description="Forget a handle and free its memory.",
        annotations=session,
    )
    def pix_release(handle: Handle) -> dict[str, Any]:
        return toolbox.release(handle)

    return server


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pix-mcp", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        help="directory the server may read and write (repeatable)",
    )
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS)
    parser.add_argument(
        "--max-response-bytes", type=int, default=DEFAULT_MAX_RESPONSE_BYTES
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    roots = list(args.root)
    if not roots and os.environ.get("PIX_MCP_ROOTS"):
        roots = [item for item in os.environ["PIX_MCP_ROOTS"].split(os.pathsep) if item]
    try:
        toolbox = PixToolbox(
            roots or None,
            max_items=args.max_items,
            max_response_bytes=args.max_response_bytes,
        )
    except ValueError as error:
        print(f"pix-mcp: {error}", file=sys.stderr)
        return 2
    build_server(toolbox).run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
