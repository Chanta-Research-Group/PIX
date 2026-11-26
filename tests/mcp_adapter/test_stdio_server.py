"""Start ``pix-mcp`` as a subprocess and call it through the MCP client."""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

EXPECTED_TOOLS = {
    "pix_capabilities",
    "pix_open_log",
    "pix_project_cases",
    "pix_inspect",
    "pix_filter",
    "pix_variants",
    "pix_discover_dfg",
    "pix_discover_ocdfg",
    "pix_case_performance",
    "pix_discover_process_model",
    "pix_load_model",
    "pix_conformance",
    "pix_export",
    "pix_list_handles",
    "pix_release",
}


def payload(result) -> dict:
    structured = getattr(result, "structuredContent", None)
    if structured is None:
        structured = getattr(result, "structured_content", None)
    if structured is not None:
        return (
            structured.get("result", structured)
            if "status" not in structured
            else structured
        )
    return json.loads(result.content[0].text)


async def session_run(root: Path) -> dict:
    src = Path(__file__).resolve().parents[2] / "src"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pix.mcp.server", "--root", str(root)],
        env={**os.environ, "PYTHONPATH": str(src)},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            opened = payload(
                await session.call_tool(
                    "pix_open_log",
                    {
                        "path": "log.csv",
                        "case_column": "case",
                        "activity_column": "activity",
                        "timestamp_column": "time",
                    },
                )
            )
            started = payload(
                await session.call_tool(
                    "pix_filter",
                    {"handle": opened["handle"], "kind": "start", "activities": ["A"]},
                )
            )
            ended = payload(
                await session.call_tool(
                    "pix_filter",
                    {"handle": started["handle"], "kind": "end", "activities": ["C"]},
                )
            )
            variants = payload(
                await session.call_tool("pix_variants", {"handle": ended["handle"]})
            )
            model = payload(
                await session.call_tool(
                    "pix_discover_process_model", {"handle": opened["handle"]}
                )
            )
            fit = payload(
                await session.call_tool(
                    "pix_conformance",
                    {"log_handle": opened["handle"], "model_handle": model["handle"]},
                )
            )
            outside = payload(
                await session.call_tool("pix_open_log", {"path": "/etc/hostname"})
            )
            return {
                "tools": listed.tools,
                "opened": opened,
                "ended": ended,
                "variants": variants,
                "fit": fit,
                "outside": outside,
            }


def test_stdio_round_trip(table_dir: Path) -> None:
    run = asyncio.run(asyncio.wait_for(session_run(table_dir), timeout=120))
    tools = {tool.name: tool for tool in run["tools"]}
    assert set(tools) == EXPECTED_TOOLS
    for tool in run["tools"]:
        assert tool.description
    assert run["opened"]["cases"] == 5
    assert run["ended"]["selected_cases"] == 3
    assert {tuple(row["activities"]) for row in run["variants"]["variants"]} == {
        ("A", "B", "C"),
        ("A", "X", "C"),
        ("A", "C"),
    }
    assert run["fit"]["status"] == "computed"
    assert run["fit"]["log_fitness"]["value"] == pytest.approx(1.0)
    assert run["outside"]["error"]["code"] == "path_outside_roots"
