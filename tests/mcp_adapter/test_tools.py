"""PixToolbox behavior as an agent sees it: handles, statuses, bounds, roots."""

import ast
import json
from pathlib import Path

import pytest

from pix.mcp.tools import FILTER_KINDS, PixToolbox
from pix.ocel import export_ocel


@pytest.fixture
def toolbox(table_dir: Path) -> PixToolbox:
    return PixToolbox([table_dir])


def open_table(toolbox: PixToolbox) -> str:
    result = toolbox.open_log(
        "log.csv",
        case_column="case",
        activity_column="activity",
        timestamp_column="time",
        resource_column="resource",
    )
    assert result["status"] == "computed", result
    return result["handle"]


def variants_of(toolbox: PixToolbox, handle: str) -> set[tuple[str, ...]]:
    listed = toolbox.variants(handle)
    assert listed["status"] == "computed"
    return {tuple(row["activities"]) for row in listed["variants"]}


def test_every_result_is_json_with_a_status(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    for result in (
        toolbox.capabilities(),
        toolbox.inspect(handle),
        toolbox.variants(handle),
        toolbox.discover_dfg(handle),
        toolbox.case_performance(handle),
        toolbox.list_handles(),
    ):
        assert result["status"] == "computed"
        json.dumps(result, allow_nan=False)


def test_open_table_requires_explicit_case_and_activity(toolbox: PixToolbox) -> None:
    refused = toolbox.open_log("log.csv")
    assert refused["status"] == "invalid_input"
    codes = [item["code"] for item in refused["evidence"]["import_issues"]["items"]]
    assert codes == ["table_mapping_required"]
    partial_mapping = toolbox.open_log("log.csv", case_column="case")
    assert partial_mapping["error"]["code"] == "mapping_incomplete"


def test_inspect_reports_counts_and_time_range(toolbox: PixToolbox) -> None:
    summary = toolbox.inspect(open_table(toolbox))
    assert (summary["cases"], summary["events"]) == (5, 14)
    assert summary["start_activities"] == [
        {"activity": "A", "cases": 4},
        {"activity": "X", "cases": 1},
    ]
    assert summary["time_range"]["first"] == "2026-01-01T09:00:00Z"
    assert summary["event_attribute_keys"]["org:resource"] == 14


def test_start_and_end_combine_by_chaining(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    started = toolbox.filter(handle, "start", activities=["A"])
    assert started["selected_cases"] == 4
    both = toolbox.filter(started["handle"], "end", activities=["C"])
    assert (both["source_cases"], both["selected_cases"]) == (4, 3)
    assert variants_of(toolbox, both["handle"]) == {
        ("A", "B", "C"),
        ("A", "X", "C"),
        ("A", "C"),
    }
    # A ... C ordering alone is a different predicate: it keeps XAC and ACD.
    ordered = toolbox.filter(handle, "eventually_follows", pattern=["A", "C"])
    assert ("X", "A", "C") in variants_of(toolbox, ordered["handle"])


def test_filter_start_and_end_kind(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    both = toolbox.filter(
        handle,
        "start_and_end",
        start_activities=["A"],
        end_activities=["C"],
    )
    assert (both["source_cases"], both["selected_cases"]) == (5, 3)
    assert variants_of(toolbox, both["handle"]) == {
        ("A", "B", "C"),
        ("A", "X", "C"),
        ("A", "C"),
    }
    chained = toolbox.filter(
        toolbox.filter(handle, "start", activities=["A"])["handle"],
        "end",
        activities=["C"],
    )
    assert variants_of(toolbox, both["handle"]) == variants_of(
        toolbox, chained["handle"]
    )


def test_filter_start_and_end_requires_boundary_lists(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    missing = toolbox.filter(handle, "start_and_end", end_activities=["C"])
    assert missing["status"] == "invalid_input"
    assert "start_activities" in missing["error"]["message"]


def test_filter_complement_attribute_and_time(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    without_x = toolbox.filter(handle, "activity", activities=["X"], positive=False)
    assert without_x["selected_cases"] == 3
    by_resource = toolbox.filter(
        handle,
        "event_attribute",
        attribute_key="org:resource",
        attribute_values=["u3"],
    )
    assert by_resource["selected_cases"] == 2
    january_3 = toolbox.filter(
        handle,
        "time",
        time_start="2026-01-03T00:00:00Z",
        time_end="2026-01-04T23:59:59+00:00",
    )
    assert january_3["selected_cases"] == 2
    naive = toolbox.filter(handle, "time", time_start="2026-01-03T00:00:00")
    assert naive["error"]["code"] == "invalid_time"


def test_filter_contract_errors_are_structured(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    assert toolbox.filter(handle, "nope")["error"]["code"] == "unknown_kind"
    wrong = toolbox.filter(handle, "directly_follows", pattern=["A"])
    assert wrong["status"] == "invalid_input"
    assert "two-activity" in wrong["error"]["message"]
    assert set(FILTER_KINDS) >= {
        "start",
        "end",
        "start_and_end",
        "variants",
        "time",
    }


def test_dfg_edges_sorted_and_capped(toolbox: PixToolbox) -> None:
    graph = toolbox.discover_dfg(open_table(toolbox), max_items=2)
    assert graph["edges"][0] == {"source": "A", "target": "C", "count": 3, "cases": 3}
    assert len(graph["edges"]) == 2 and graph["truncated"] is True
    assert graph["edge_count"] > 2


def test_performance_uses_seconds(toolbox: PixToolbox) -> None:
    performance = toolbox.case_performance(open_table(toolbox), max_items=1)
    assert performance["duration_seconds"]["maximum"] == 10800.0
    assert performance["slowest_cases"][0]["case_id"] == "2"


def test_discovered_model_fits_its_own_log(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    model = toolbox.discover_process_model(handle)
    assert model["status"] == "computed"
    assert model["handle"].startswith("model-")
    for method in ("alignment", "token"):
        fit = toolbox.conformance(handle, model["handle"], method=method)
        assert fit["status"] == "computed"
        assert fit["log_fitness"]["value"] == pytest.approx(1.0)


def test_alignment_reports_deviations(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    clean = toolbox.filter(handle, "variants", variants=[["A", "B", "C"]])
    model = toolbox.discover_process_model(clean["handle"])
    fit = toolbox.conformance(handle, model["handle"])
    assert fit["status"] == "computed"
    assert fit["log_fitness"]["value"] < 1
    assert fit["deviations"]["log_moves"]["X"] == 2
    assert fit["deviations"]["model_moves"]["B"] == 4


def test_model_round_trip_through_files(toolbox: PixToolbox, tmp_path: Path) -> None:
    handle = open_table(toolbox)
    model = toolbox.discover_process_model(handle)
    for name in ("model.pnml", "model.ptml", "model.json"):
        written = toolbox.export(model["handle"], name)
        assert written["status"] == "computed", written
        loaded = toolbox.load_model(str(tmp_path / name))
        assert loaded["conformance_ready"] is True
        fit = toolbox.conformance(handle, loaded["handle"])
        assert fit["log_fitness"]["value"] == pytest.approx(1.0)


def test_export_refuses_overwrite_and_source(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    first = toolbox.export(handle, "out.xes")
    assert first["status"] == "computed"
    assert toolbox.export(handle, "out.xes")["error"]["code"] == "exists"
    assert toolbox.export(handle, "out.xes", overwrite=True)["status"] == "computed"
    protected = toolbox.export(handle, "log.csv", overwrite=True)
    assert protected["error"]["code"] == "protected"
    reopened = toolbox.open_log("out.xes")
    assert (reopened["kind"], reopened["cases"]) == ("case_log", 5)


def test_paths_stay_inside_roots(toolbox: PixToolbox, tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.csv"
    for path in (str(outside), "../outside.csv", "/etc/hostname"):
        assert toolbox.open_log(path)["error"]["code"] == "path_outside_roots"
    assert toolbox.open_log("https://example.com/x.xes")["error"]["code"] == (
        "remote_input"
    )
    link = tmp_path / "escape.xes"
    link.symlink_to(outside)
    assert toolbox.open_log("escape.xes")["error"]["code"] == "path_outside_roots"
    assert toolbox.export(open_table(toolbox), "../x.xes")["error"]["code"] == (
        "path_outside_roots"
    )


def test_ocel_projection_and_ocdfg(tmp_path: Path, native_log) -> None:
    export_ocel(native_log, tmp_path / "log.jsonocel", format="json")
    toolbox = PixToolbox([tmp_path])
    opened = toolbox.open_log("log.jsonocel")
    assert (opened["kind"], opened["events"], opened["objects"]) == ("ocel", 7, 6)
    summary = toolbox.inspect(opened["handle"])
    assert summary["object_types"]["Order"] == 3
    assert toolbox.variants(opened["handle"])["error"]["code"] == "wrong_handle_kind"
    graph = toolbox.discover_ocdfg(opened["handle"], ["Order", "Package"])
    assert graph["status"] == "computed"
    assert [g["object_type"] for g in graph["graphs"]] == ["Order", "Package"]
    projected = toolbox.project_cases(opened["handle"], "Order")
    assert projected["cases"] == 3
    assert {("Create", "Pack", "Ship"), ("Create", "Ship")} == variants_of(
        toolbox, projected["handle"]
    )


def test_handles_are_bounded_and_releasable(table_dir: Path) -> None:
    toolbox = PixToolbox([table_dir], max_handles=2)
    handles = [open_table(toolbox) for _ in range(3)]
    assert toolbox.inspect(handles[0])["error"]["code"] == "unknown_handle"
    assert toolbox.release(handles[2])["released"] == handles[2]
    assert [row["handle"] for row in toolbox.list_handles()["handles"]] == [handles[1]]


def test_response_size_limit(table_dir: Path) -> None:
    toolbox = PixToolbox([table_dir], max_response_bytes=300)
    handle = open_table_small(toolbox)
    assert toolbox.discover_dfg(handle)["error"]["code"] == "response_too_large"


def open_table_small(toolbox: PixToolbox) -> str:
    toolbox.max_response_bytes, limit = 1_000_000, toolbox.max_response_bytes
    handle = open_table(toolbox)
    toolbox.max_response_bytes = limit
    return handle


def test_tool_core_does_not_import_the_mcp_sdk() -> None:
    source = Path(__file__).resolve().parents[2] / "src" / "pix" / "mcp" / "tools.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "mcp" not in roots and "pydantic" not in roots


def test_bpmn_model_is_compiled_by_pix(toolbox: PixToolbox, tmp_path: Path) -> None:
    from pix.case_centric.inductive import discover_inductive
    from pix.case_centric.model_conversion import tree_to_bpmn
    from pix.model_io import write_bpmn

    handle = open_table(toolbox)
    log = toolbox._case_log(handle)
    write_bpmn(
        tree_to_bpmn(discover_inductive(log)).value.model, tmp_path / "model.bpmn"
    )
    loaded = toolbox.load_model("model.bpmn")
    assert (loaded["model_type"], loaded["conformance_ready"]) == ("bpmn", True)
    fit = toolbox.conformance(handle, loaded["handle"])
    assert fit["status"] == "computed"
    assert fit["log_fitness"]["value"] == pytest.approx(1.0)


def test_unknown_model_suffix_and_missing_net(
    toolbox: PixToolbox, tmp_path: Path
) -> None:
    (tmp_path / "model.txt").write_text("x", encoding="utf-8")
    assert toolbox.load_model("model.txt")["error"]["code"] == "unsupported_format"
    handle = open_table(toolbox)
    assert toolbox.conformance(handle, handle)["error"]["code"] == "wrong_handle_kind"


def test_performance_budget_is_reported_not_guessed(toolbox: PixToolbox) -> None:
    handle = open_table(toolbox)
    bounded = toolbox.case_performance(handle, max_interval_pairs=1)
    assert bounded["status"] == "unavailable"
    assert "interval_limit" in bounded["issues"]["by_code"]
    assert "duration_seconds" not in bounded
    assert toolbox.case_performance(handle, max_interval_pairs=0)["error"]["code"] == (
        "invalid_limit"
    )
