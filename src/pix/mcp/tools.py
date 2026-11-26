"""Agent-facing PIX tools with bounded, structured JSON results.

This module has no MCP dependency. ``PixToolbox`` keeps opened logs and
models in an in-process handle table so that agents pass short handles
between calls instead of re-sending data. Every public method returns a
JSON-compatible ``dict`` with a ``status`` field:

``computed``      the PIX operator finished on the whole input
``partial``       PIX returned a bounded or lower-bound result; read ``issues``
``invalid_input`` the request or the data does not meet the operator contract
``unavailable``   PIX does not provide this computation for this input
``error``         the adapter refused the request (path, handle, size limits)

Files are read and written only below the configured roots. The adapter only
calls PIX operators; it never substitutes another library or a heuristic for
an operation PIX does not implement.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections import Counter, OrderedDict
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from fractions import Fraction
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Sequence

from pix import __version__

ADAPTER_VERSION = "1.0.0"
DEFAULT_MAX_ITEMS = 50
HARD_MAX_ITEMS = 1000
DEFAULT_MAX_RESPONSE_BYTES = 256_000
DEFAULT_MAX_HANDLES = 32
_MAX_ACTIVITIES_PER_VARIANT = 200
MAX_INTERVAL_PAIRS = 100_000_000

FILTER_KINDS = (
    "activity",
    "start",
    "end",
    "start_and_end",
    "event_attribute",
    "case_attribute",
    "attribute_frequency",
    "variants",
    "variant_frequency",
    "length",
    "duration",
    "rework",
    "directly_follows",
    "eventually_follows",
    "sequence",
    "prefix",
    "suffix",
    "time",
    "path_duration",
    "four_eyes",
    "different_resources",
    "case_limit",
)


class ToolError(Exception):
    """A refused request; reported as ``status: error`` with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _json(value: object, depth: int = 0) -> object:
    """Encode PIX values (dataclasses, enums, ratios, UTC times) as JSON data."""
    if depth > 64:
        raise ToolError("nesting_limit", "result exceeds the nesting limit")
    if isinstance(value, Enum):
        return _json(value.value, depth + 1)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if value == value and abs(value) != float("inf") else None
    if isinstance(value, Fraction):
        return _ratio((value.numerator, value.denominator))
    if isinstance(value, os.PathLike):
        return os.fspath(value)
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, (tuple, list, frozenset, set)):
        items = (
            sorted(value, key=repr) if isinstance(value, (set, frozenset)) else value
        )
        return [_json(item, depth + 1) for item in items]
    if isinstance(value, dict):
        return {str(key): _json(item, depth + 1) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json(getattr(value, field.name), depth + 1)
            for field in fields(value)
        }
    return repr(value)


def _ratio(value: object) -> dict[str, object] | None:
    """PIX keeps exact ratios as (numerator, denominator); keep both."""
    if value is None:
        return None
    if isinstance(value, Fraction):
        value = (value.numerator, value.denominator)
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and all(type(item) is int for item in value)
    ):
        numerator, denominator = value
        return {
            "numerator": numerator,
            "denominator": denominator,
            "value": numerator / denominator if denominator else None,
        }
    return _json(value)


def _compact(value: object, limit: int) -> object:
    """Replace long lists inside an encoded receipt by a count and a prefix."""
    if isinstance(value, list):
        if len(value) > limit:
            return {"count": len(value), "first": value[:limit], "truncated": True}
        return [_compact(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: _compact(item, limit) for key, item in value.items()}
    return value


def _cap(items: Sequence[object], limit: int) -> tuple[list[object], bool]:
    items = list(items)
    return items[:limit], len(items) > limit


def _issues(issues: Sequence[object], limit: int) -> dict[str, object]:
    """Summarize PIX ComputeIssue tuples: counts by code plus the first few."""
    issues = tuple(issues)
    shown, truncated = _cap(issues, limit)
    return {
        "count": len(issues),
        "by_code": dict(Counter(issue.code for issue in issues)),
        "items": [
            {"code": issue.code, "message": issue.message, "at": list(issue.at)}
            for issue in shown
        ],
        "truncated": truncated,
    }


def _envelope(result: object, limit: int) -> dict[str, object]:
    return {
        "status": result.status.value,
        "operator": result.operator_id,
        "computation_id": result.computation_id,
        "issues": _issues(result.issues, limit),
    }


@dataclass
class _Entry:
    handle: str
    kind: str
    value: object
    origin: dict[str, object]
    extra: dict[str, object]


def _tool(method: Callable[..., dict[str, object]]):
    """Turn refusals and contract errors into structured, size-bounded results."""

    @wraps(method)
    def wrapper(self: PixToolbox, *args: Any, **kwargs: Any) -> dict[str, object]:
        try:
            with self._lock:
                payload = method(self, *args, **kwargs)
        except ToolError as error:
            payload = {
                "status": "error",
                "error": {"code": error.code, "message": error.message},
            }
        except (ValueError, TypeError) as error:
            payload = {
                "status": "invalid_input",
                "error": {"code": type(error).__name__, "message": str(error)},
            }
        except OSError as error:
            payload = {
                "status": "error",
                "error": {"code": "os_error", "message": str(error)},
            }
        except Exception as error:  # report, never crash the server session
            payload = {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": f"{type(error).__name__}: {error}",
                },
            }
        payload = _json(payload)
        size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        if size > self.max_response_bytes:
            payload = {
                "status": "error",
                "error": {
                    "code": "response_too_large",
                    "message": (
                        f"result is {size} bytes, above the "
                        f"{self.max_response_bytes}-byte limit; lower max_items "
                        "or filter the log first"
                    ),
                },
            }
        return payload

    return wrapper


class PixToolbox:
    """In-process PIX session: allowed roots, handle table, output limits."""

    def __init__(
        self,
        roots: Sequence[str | os.PathLike[str]] | None = None,
        *,
        max_items: int = DEFAULT_MAX_ITEMS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        max_handles: int = DEFAULT_MAX_HANDLES,
    ) -> None:
        selected = list(roots) if roots else [os.getcwd()]
        self.roots = tuple(Path(root).expanduser().resolve() for root in selected)
        for root in self.roots:
            if not root.is_dir():
                raise ValueError(f"allowed root is not a directory: {root}")
        if not 1 <= max_items <= HARD_MAX_ITEMS:
            raise ValueError(f"max_items must be between 1 and {HARD_MAX_ITEMS}")
        self.default_max_items = max_items
        self.max_response_bytes = max_response_bytes
        self.max_handles = max_handles
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self._lock = threading.RLock()
        self._counter = 0

    # ----------------------------------------------------------- helpers
    def _limit(self, max_items: int | None) -> int:
        if max_items is None:
            return self.default_max_items
        if type(max_items) is not int or not 1 <= max_items <= HARD_MAX_ITEMS:
            raise ToolError(
                "invalid_limit", f"max_items must be between 1 and {HARD_MAX_ITEMS}"
            )
        return max_items

    def _inside(self, path: Path) -> bool:
        return any(path == root or root in path.parents for root in self.roots)

    def _resolve(self, path: str) -> Path:
        if not isinstance(path, str) or not path.strip():
            raise ToolError("invalid_path", "path must be a nonempty string")
        if "://" in path:
            raise ToolError(
                "remote_input",
                "PIX reads local files only; download the data first, then pass "
                "its local path",
            )
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.roots[0] / candidate
        resolved = candidate.resolve()
        if not self._inside(resolved):
            raise ToolError(
                "path_outside_roots",
                f"{path} is outside the allowed roots "
                f"{[str(root) for root in self.roots]}",
            )
        return resolved

    def _input_path(self, path: str) -> Path:
        resolved = self._resolve(path)
        if not resolved.is_file():
            raise ToolError("not_found", f"no such file: {resolved}")
        return resolved

    def _output_path(self, path: str, overwrite: bool) -> Path:
        if type(overwrite) is not bool:
            raise ToolError("invalid_argument", "overwrite must be true or false")
        resolved = self._resolve(path)
        if not resolved.parent.is_dir():
            raise ToolError(
                "not_found", f"output directory does not exist: {resolved.parent}"
            )
        if resolved.exists() and not overwrite:
            raise ToolError(
                "exists", f"{resolved} exists; pass overwrite=true to replace it"
            )
        sources = {
            entry.origin.get("path")
            for entry in self._entries.values()
            if entry.origin.get("path")
        }
        if str(resolved) in sources:
            raise ToolError("protected", "refusing to overwrite an opened source file")
        return resolved

    def _store(
        self, kind: str, value: object, origin: dict[str, object], **extra: object
    ) -> _Entry:
        self._counter += 1
        prefix = "model" if kind == "model" else "log"
        entry = _Entry(f"{prefix}-{self._counter}", kind, value, origin, dict(extra))
        self._entries[entry.handle] = entry
        while len(self._entries) > self.max_handles:
            self._entries.popitem(last=False)
        return entry

    def _get(self, handle: str, *kinds: str) -> _Entry:
        entry = self._entries.get(handle) if isinstance(handle, str) else None
        if entry is None:
            raise ToolError(
                "unknown_handle",
                f"unknown handle {handle!r}; open the file again or call "
                "pix_list_handles",
            )
        self._entries.move_to_end(handle)
        if kinds and entry.kind not in kinds:
            raise ToolError(
                "wrong_handle_kind",
                f"{handle} is a {entry.kind}; this tool needs {' or '.join(kinds)}"
                + (
                    " (project an OCEL log with pix_project_cases first)"
                    if entry.kind == "ocel" and "case_log" in kinds
                    else ""
                ),
            )
        return entry

    def _case_log(self, handle: str):
        return self._get(handle, "case_log").value

    @staticmethod
    def _describe(entry: _Entry) -> dict[str, object]:
        summary: dict[str, object] = {
            "handle": entry.handle,
            "kind": entry.kind,
            "origin": entry.origin,
        }
        if entry.kind == "case_log":
            summary["cases"] = len(entry.value.traces)
            summary["events"] = sum(len(trace.events) for trace in entry.value.traces)
        elif entry.kind == "ocel":
            summary["events"] = len(entry.value.events)
            summary["objects"] = len(entry.value.objects)
        else:
            summary["model_type"] = entry.extra.get("model_type")
        return summary

    # ------------------------------------------------------------- tools
    @_tool
    def capabilities(self) -> dict[str, object]:
        """Describe the adapter, its limits and the PIX operator behind each tool."""
        return {
            "status": "computed",
            "pix_version": __version__,
            "adapter_version": ADAPTER_VERSION,
            "allowed_roots": [str(root) for root in self.roots],
            "limits": {
                "default_max_items": self.default_max_items,
                "hard_max_items": HARD_MAX_ITEMS,
                "max_response_bytes": self.max_response_bytes,
                "max_handles": self.max_handles,
            },
            "input_formats": [
                "XES / XES.gz",
                "MXML / MXML.gz",
                "OCEL 2.0 JSON, XML, SQLite",
                "CSV / TSV / XLSX with explicit case and activity columns",
            ],
            "model_formats": ["PNML", "PTML", "BPMN", "PIX model JSON"],
            "operators": {
                "pix_open_log": "pix.io.import_log",
                "pix_project_cases": "pix.object_centric.project_object_cases",
                "pix_filter": "pix.case_centric.filtering.filter_case_log",
                "pix_variants": "pix.case_centric.trace_catalog.catalog_trace_variants",
                "pix_discover_dfg": "pix.case_centric.discovery.discover_dfg",
                "pix_discover_ocdfg": "pix.api.discover_ocdfg",
                "pix_case_performance": (
                    "pix.case_centric.statistics.measure_case_performance"
                ),
                "pix_discover_process_model": (
                    "pix.case_centric.inductive.discover_inductive"
                ),
                "pix_conformance": (
                    "pix.case_centric.conformance.measure_alignment_fitness / "
                    "measure_token_fitness, pix.case_centric.execution.align_traces"
                ),
                "pix_export": "pix.event_log.write_xes, pix.ocel.export_ocel, "
                "pix.model_io.write_pnml / write_ptml / write_bpmn",
            },
            "filter_kinds": list(FILTER_KINDS),
            "notes": [
                "Case-centric tools need a case log. Project OCEL logs to one "
                "object type with pix_project_cases first.",
                "Each pix_filter call applies one predicate. Call it again on the "
                "returned handle to combine predicates, or use kind=start_and_end "
                "with start_activities and end_activities for boundary conjunction.",
                "Operations outside this list are not approximated. Use the PIX "
                "Python API, or treat the result as unavailable.",
            ],
        }

    @_tool
    def open_log(
        self,
        path: str,
        format: str | None = None,
        case_column: str | None = None,
        activity_column: str | None = None,
        timestamp_column: str | None = None,
        resource_column: str | None = None,
        event_id_column: str | None = None,
        order: str = "source",
        reject_timezone_assumptions: bool = False,
        max_items: int | None = None,
    ) -> dict[str, object]:
        """Import an event log file and return a handle plus import evidence."""
        from pix.event_log import CaseImportResult
        from pix.io import import_log
        from pix.tabular import AttributeColumn, CaseTableMapping

        limit = self._limit(max_items)
        source = self._input_path(path)
        mapping = None
        columns = (case_column, activity_column, timestamp_column, resource_column)
        if any(column is not None for column in (*columns, event_id_column)):
            if not case_column or not activity_column:
                raise ToolError(
                    "mapping_incomplete",
                    "tables need both case_column and activity_column; PIX does "
                    "not guess the case notion",
                )
            mapping = CaseTableMapping(
                case_column,
                activity_column,
                timestamp_column,
                event_id_column,
                event_attributes=(
                    (AttributeColumn(resource_column, "string", "org:resource"),)
                    if resource_column
                    else ()
                ),
                order=order,
            )
        imported = import_log(str(source), format=format, mapping=mapping)
        described = imported.describe()
        evidence = {
            "format": described.get("format"),
            "source_sha256": described.get("sourceSha256"),
            "source_size": described.get("sourceSize"),
            "transformations": [
                {"code": item.get("code"), "message": item.get("message")}
                for item in described.get("transformations", ())
            ][:limit],
        }
        import_issues = list(described.get("issues", ()))
        shown, truncated = _cap(import_issues, limit)
        evidence["import_issues"] = {
            "count": len(import_issues),
            "items": shown,
            "truncated": truncated,
        }
        if not imported.valid:
            return {
                "status": "invalid_input",
                "import_status": described.get("status"),
                "evidence": evidence,
            }
        origin = {"tool": "pix_open_log", "path": str(source)}
        if isinstance(imported, CaseImportResult):
            entry = self._store("case_log", imported.require_case_log(), origin)
        else:
            log = imported.require_ocel(
                reject_timezone_assumptions=bool(reject_timezone_assumptions)
            )
            warnings = [
                {"code": issue.code, "message": issue.message}
                for issue in getattr(log, "warnings", ())
            ]
            evidence["warnings"] = warnings[:limit]
            entry = self._store("ocel", log, origin)
        return {"status": "computed", **self._describe(entry), "evidence": evidence}

    @_tool
    def project_cases(
        self, handle: str, object_type: str, tie_policy: str = "reject"
    ) -> dict[str, object]:
        """Project an OCEL log to a case log with one case per object."""
        from pix.object_centric.case_projection import (
            ObjectCaseProjectionSpec,
            project_object_cases,
        )

        entry = self._get(handle, "ocel")
        projection = project_object_cases(
            entry.value, ObjectCaseProjectionSpec(object_type, tie_policy)
        )
        derived = self._store(
            "case_log",
            projection.case_log,
            {
                "tool": "pix_project_cases",
                "parent": handle,
                "object_type": object_type,
                "tie_policy": tie_policy,
            },
        )
        return {
            "status": "computed",
            **self._describe(derived),
            "projection": projection.describe(),
        }

    @_tool
    def inspect(self, handle: str, max_items: int | None = None) -> dict[str, object]:
        """Summarize a handle: sizes, activities, start/end counts, time range."""
        limit = self._limit(max_items)
        entry = self._get(handle)
        summary = self._describe(entry)
        if entry.kind == "case_log":
            from pix.case_centric.discovery import discover_dfg

            log = entry.value
            graph = discover_dfg(log)
            times = []
            event_keys: Counter[str] = Counter()
            case_keys: Counter[str] = Counter()
            for trace in log.traces:
                case_keys.update(attribute.key for attribute in trace.attributes)
                for event in trace.events:
                    for attribute in event.attributes:
                        event_keys[attribute.key] += 1
                        if attribute.key == "time:timestamp" and isinstance(
                            attribute.value, datetime
                        ):
                            times.append(attribute.value)
            value = graph.value
            activities, more = _cap(
                sorted(value.activity_counts, key=lambda item: (-item[1], item[0])),
                limit,
            )
            summary.update(
                status=graph.status.value,
                empty_cases=value.empty_trace_count,
                activity_count=len(value.activity_counts),
                activities=[{"activity": a, "events": n} for a, n in activities],
                activities_truncated=more,
                start_activities=[
                    {"activity": a, "cases": n} for a, n in value.start_counts[:limit]
                ],
                end_activities=[
                    {"activity": a, "cases": n} for a, n in value.end_counts[:limit]
                ],
                time_range=(
                    {
                        "first": min(times),
                        "last": max(times),
                        "events_with_time": len(times),
                    }
                    if times
                    else None
                ),
                event_attribute_keys=dict(event_keys.most_common(limit)),
                case_attribute_keys=dict(case_keys.most_common(limit)),
                issues=_issues(graph.issues, limit),
            )
        elif entry.kind == "ocel":
            log = entry.value
            event_types = Counter(event.type for event in log.events)
            object_types = Counter(obj.type for obj in log.objects)
            times = [event.time for event in log.events]
            summary.update(
                status="computed",
                event_types=dict(event_types.most_common(limit)),
                object_types=dict(object_types.most_common(limit)),
                e2o_relations=len(log.e2o),
                o2o_relations=len(log.o2o),
                time_range=(
                    {"first": min(times), "last": max(times)} if times else None
                ),
            )
        else:
            summary.update(status="computed", **entry.extra)
        return summary

    @_tool
    def filter(
        self,
        handle: str,
        kind: str,
        activities: list[str] | None = None,
        start_activities: list[str] | None = None,
        end_activities: list[str] | None = None,
        pattern: list[str] | None = None,
        variants: list[list[str]] | None = None,
        minimum: float | None = None,
        maximum: float | None = None,
        time_start: str | None = None,
        time_end: str | None = None,
        time_mode: str | None = None,
        mode: str | None = None,
        quantifier: str | None = None,
        positive: bool = True,
        top_k: int | None = None,
        cumulative_coverage: float | None = None,
        attribute_key: str | None = None,
        attribute_operator: str = "equals",
        attribute_values: list[Any] | None = None,
        attribute_value_type: str = "string",
        attribute_minimum: float | None = None,
        attribute_maximum: float | None = None,
        max_items: int | None = None,
    ) -> dict[str, object]:
        """Apply one PIX case filter and return a handle to the selected log."""
        from pix.case_centric.filtering import (
            AttributeCondition,
            CaseFilterSpec,
            FilterScalar,
            filter_case_log,
            materialize_case_selection,
        )

        limit = self._limit(max_items)
        log = self._case_log(handle)
        if kind not in FILTER_KINDS:
            raise ToolError("unknown_kind", f"kind must be one of {list(FILTER_KINDS)}")
        options: dict[str, object] = {"kind": kind, "positive": bool(positive)}
        if activities:
            options["activities"] = tuple(activities)
        if start_activities:
            options["start_activities"] = tuple(start_activities)
        if end_activities:
            options["end_activities"] = tuple(end_activities)
        if pattern:
            options["pattern"] = tuple(pattern)
        if variants:
            options["variants"] = tuple(tuple(variant) for variant in variants)
        for name, value in (
            ("minimum", minimum),
            ("maximum", maximum),
            ("time_mode", time_mode),
            ("mode", mode),
            ("quantifier", quantifier),
            ("top_k", top_k),
            ("cumulative_coverage", cumulative_coverage),
        ):
            if value is not None:
                options[name] = value
        for name, value in (("time_start", time_start), ("time_end", time_end)):
            if value is not None:
                options[name] = _parse_time(value, name)
        if attribute_key is not None:
            scalars = tuple(
                _scalar(item, attribute_value_type, FilterScalar)
                for item in (attribute_values or ())
            )
            options["attribute"] = AttributeCondition(
                attribute_key,
                attribute_operator,
                scalars,
                attribute_minimum,
                attribute_maximum,
            )
        spec = CaseFilterSpec(**options)
        selection = filter_case_log(log, spec)
        payload = _envelope(selection, limit)
        if selection.value is None or selection.status.value not in (
            "computed",
            "partial",
        ):
            return payload
        derived_log = materialize_case_selection(log, selection)
        value = selection.value
        derived = self._store(
            "case_log",
            derived_log,
            {"tool": "pix_filter", "parent": handle, "kind": kind},
        )
        payload.update(
            handle=derived.handle,
            parent=handle,
            source_cases=value.source_case_count,
            source_events=value.source_event_count,
            selected_cases=value.selected_source_case_count,
            selected_events=value.selected_event_count,
            excluded_cases=len(value.excluded_case_ids),
            unknown_cases=len(value.unknown_case_ids),
            unknown_events=len(value.unknown_event_ids),
        )
        return payload

    @_tool
    def variants(self, handle: str, max_items: int | None = None) -> dict[str, object]:
        """List exact activity variants by frequency (rank 1 is most frequent)."""
        from pix.case_centric.trace_catalog import catalog_trace_variants

        limit = self._limit(max_items)
        log = self._case_log(handle)
        result = catalog_trace_variants(log)
        payload = _envelope(result, limit)
        if result.value is None:
            return payload
        total = len(log.traces)
        rows = []
        shown, truncated = _cap(result.value.variants, limit)
        for variant in shown:
            activities, long_variant = _cap(
                variant.activities, _MAX_ACTIVITIES_PER_VARIANT
            )
            rows.append(
                {
                    "rank": variant.rank,
                    "cases": len(variant.case_ids),
                    "case_share": len(variant.case_ids) / total if total else None,
                    "length": len(variant.activities),
                    "activities": activities,
                    "activities_truncated": long_variant,
                    "example_case_id": variant.example_case_id,
                }
            )
        payload.update(
            cases=total,
            variant_count=len(result.value.variants),
            variants=rows,
            truncated=truncated,
        )
        return payload

    @_tool
    def discover_dfg(
        self,
        handle: str,
        counting: str = "occurrences",
        max_items: int | None = None,
    ) -> dict[str, object]:
        """Directly-follows graph of a case log, edges sorted by frequency."""
        from pix.case_centric.discovery import RelationDiscoverySpec, discover_dfg

        limit = self._limit(max_items)
        result = discover_dfg(self._case_log(handle), RelationDiscoverySpec(counting))
        payload = _envelope(result, limit)
        graph = result.value
        if graph is None:
            return payload
        edges, truncated = _cap(
            sorted(
                graph.edges,
                key=lambda edge: (-edge.count, edge.source, edge.target),
            ),
            limit,
        )
        payload.update(
            counting=counting,
            cases=graph.trace_count,
            empty_cases=graph.empty_trace_count,
            complete=graph.complete,
            activities=[{"activity": a, "count": n} for a, n in graph.activity_counts],
            start_activities=[
                {"activity": a, "count": n} for a, n in graph.start_counts
            ],
            end_activities=[{"activity": a, "count": n} for a, n in graph.end_counts],
            edge_count=len(graph.edges),
            edges=[
                {
                    "source": edge.source,
                    "target": edge.target,
                    "count": edge.count,
                    "cases": edge.case_count,
                }
                for edge in edges
            ],
            truncated=truncated,
        )
        return payload

    @_tool
    def discover_ocdfg(
        self,
        handle: str,
        object_types: list[str],
        max_items: int | None = None,
    ) -> dict[str, object]:
        """Object-centric DFG: one directly-follows graph per object type."""
        from pix.api import OCDFGSpec, discover_ocdfg

        limit = self._limit(max_items)
        entry = self._get(handle, "ocel")
        if not object_types:
            raise ToolError(
                "invalid_argument", "object_types must name at least one type"
            )
        result = discover_ocdfg(entry.value, OCDFGSpec(tuple(object_types)))
        payload = _envelope(result, limit)
        if result.value is None:
            return payload
        graphs = []
        for graph in result.value.graphs:
            edges, truncated = _cap(
                sorted(
                    graph.edges,
                    key=lambda edge: (
                        -edge.event_pair_count,
                        edge.source_activity,
                        edge.target_activity,
                    ),
                ),
                limit,
            )
            graphs.append(
                {
                    "object_type": graph.object_type,
                    "objects": graph.object_count,
                    "objects_without_events": len(graph.empty_object_ids),
                    "activities": [
                        {
                            "activity": row.activity,
                            "event_occurrences": row.event_occurrence_count,
                            "objects": len(row.object_ids),
                        }
                        for row in graph.activities
                    ][:limit],
                    "starts": _json(graph.starts[:limit]),
                    "ends": _json(graph.ends[:limit]),
                    "edge_count": len(graph.edges),
                    "edges": [
                        {
                            "source": edge.source_activity,
                            "target": edge.target_activity,
                            "event_pairs": edge.event_pair_count,
                            "objects": edge.unique_object_count,
                        }
                        for edge in edges
                    ],
                    "truncated": truncated,
                }
            )
        payload["graphs"] = graphs
        return payload

    @_tool
    def case_performance(
        self,
        handle: str,
        max_interval_pairs: int = 1_000_000,
        max_items: int | None = None,
    ) -> dict[str, object]:
        """Observed case durations (seconds), arrival gaps and the slowest cases."""
        from pix.case_centric.statistics import (
            CasePerformanceSpec,
            measure_case_performance,
        )

        limit = self._limit(max_items)
        if (
            type(max_interval_pairs) is not int
            or not 1 <= max_interval_pairs <= MAX_INTERVAL_PAIRS
        ):
            raise ToolError(
                "invalid_limit",
                f"max_interval_pairs must be between 1 and {MAX_INTERVAL_PAIRS}",
            )
        result = measure_case_performance(
            self._case_log(handle),
            CasePerformanceSpec(max_interval_pairs=max_interval_pairs),
        )
        payload = _envelope(result, limit)
        value = result.value
        if value is None:
            return payload
        observed = [case for case in value.cases if case.duration_seconds is not None]
        slowest, truncated = _cap(
            sorted(observed, key=lambda case: (-case.duration_seconds, case.case_id)),
            limit,
        )
        payload.update(
            cases=len(value.cases),
            cases_with_duration=len(observed),
            case_status_counts=dict(Counter(case.status for case in value.cases)),
            duration_seconds=_json(value.duration_summary),
            arrival_gap_seconds=_json(value.arrival_summary),
            completion_gap_seconds=_json(value.completion_summary),
            slowest_cases=[
                {
                    "case_id": case.case_id,
                    "start": case.start,
                    "end": case.end,
                    "duration_seconds": case.duration_seconds,
                }
                for case in slowest
            ],
            truncated=truncated,
        )
        return payload

    @_tool
    def discover_process_model(
        self,
        handle: str,
        variant: str = "im",
        noise_threshold: float = 0.0,
        max_items: int | None = None,
    ) -> dict[str, object]:
        """Inductive Miner (im, imf, imd) process tree, kept as a model handle."""
        from pix.api import process_tree_to_petri_net
        from pix.case_centric.inductive import InductiveSpec, discover_inductive

        limit = self._limit(max_items)
        result = discover_inductive(
            self._case_log(handle),
            InductiveSpec(variant=variant, noise_threshold=noise_threshold),
        )
        payload = _envelope(result, limit)
        if result.value is None:
            return payload
        net = process_tree_to_petri_net(result.value)
        text = _tree_text(result.value)
        entry = self._store(
            "model",
            {"tree": result.value, "net": net},
            {
                "tool": "pix_discover_process_model",
                "parent": handle,
                "variant": variant,
            },
            model_type="process_tree",
            places=len(net.places),
            transitions=len(net.transitions),
            arcs=len(net.arcs),
        )
        payload.update(
            handle=entry.handle,
            process_tree=text if len(text) <= 20_000 else text[:20_000] + "…",
            petri_net={
                "places": len(net.places),
                "transitions": len(net.transitions),
                "arcs": len(net.arcs),
            },
        )
        return payload

    @_tool
    def load_model(self, path: str) -> dict[str, object]:
        """Load a PNML, PTML, BPMN or PIX model JSON file as a model handle."""
        from pix.api import process_tree_to_petri_net
        from pix.contracts.discovery import ProcessTree
        from pix.contracts.models import PetriNet

        source = self._input_path(path)
        name = source.name.lower()
        origin = {"tool": "pix_load_model", "path": str(source)}
        if name.endswith(".pnml"):
            from pix.model_io import read_pnml

            model, model_type = read_pnml(source).model, "petri_net"
        elif name.endswith(".ptml"):
            from pix.model_io import read_ptml

            model, model_type = read_ptml(source).model, "process_tree"
        elif name.endswith(".bpmn"):
            from pix.model_io import read_bpmn

            model, model_type = read_bpmn(source).model, "bpmn"
        elif name.endswith(".json"):
            from pix.models import read_model

            model = read_model(source).model
            model_type = {PetriNet: "petri_net", ProcessTree: "process_tree"}.get(
                type(model), type(model).__name__
            )
        else:
            raise ToolError(
                "unsupported_format",
                "model files must end in .pnml, .ptml, .bpmn or .json",
            )
        value: dict[str, object] = {"source": model}
        notes = []
        if model_type == "petri_net":
            value["net"] = model
        elif model_type == "process_tree":
            value["tree"] = model
            value["net"] = process_tree_to_petri_net(model)
        elif model_type == "bpmn":
            from pix.case_centric.bpmn_conversion import bpmn_to_petri_net

            converted = bpmn_to_petri_net(model)
            if converted.value is not None:
                value["net"] = converted.value.model
            else:
                notes.append(
                    {
                        "code": "bpmn_conversion_" + converted.status.value,
                        "message": "; ".join(i.message for i in converted.issues)[
                            :2000
                        ],
                    }
                )
        net = value.get("net")
        extra = {"model_type": model_type, "conformance_ready": net is not None}
        if net is not None:
            extra.update(
                places=len(net.places),
                transitions=len(net.transitions),
                arcs=len(net.arcs),
            )
        entry = self._store("model", value, origin, **extra)
        return {"status": "computed", **self._describe(entry), **extra, "notes": notes}

    @_tool
    def conformance(
        self,
        log_handle: str,
        model_handle: str,
        method: str = "alignment",
        max_states: int = 10_000,
        include_deviations: bool = True,
        max_items: int | None = None,
    ) -> dict[str, object]:
        """Fitness of a case log against a model by optimal alignment or token replay."""
        from pix.case_centric.conformance import (
            AlignmentFitnessSpec,
            measure_alignment_fitness,
            measure_token_fitness,
        )
        from pix.case_centric.execution import align_traces
        from pix.contracts.conformance import AlignmentSpec

        limit = self._limit(max_items)
        log = self._case_log(log_handle)
        model = self._get(model_handle, "model")
        net = model.value.get("net")
        if net is None:
            return {
                "status": "unavailable",
                "error": {
                    "code": "no_petri_net",
                    "message": f"{model_handle} has no Petri net semantics in PIX "
                    "(see its load notes); conformance was not computed",
                },
            }
        if method == "alignment":
            spec = AlignmentSpec(max_states=max_states)
            result = measure_alignment_fitness(log, net, AlignmentFitnessSpec(spec))
            payload = _envelope(result, limit)
            value = result.value
            if value is None:
                return payload
            worst, truncated = _cap(
                sorted(
                    value.traces,
                    key=lambda row: (
                        _ratio(row.fitness_ratio)["value"]
                        if row.fitness_ratio
                        else -1.0,
                        row.case_id,
                    ),
                ),
                limit,
            )
            payload.update(
                method="alignment",
                requested_cases=value.requested_count,
                defined_cases=value.defined_count,
                log_fitness=_ratio(value.whole_log_fitness_ratio),
                completed_log_fitness=_ratio(value.completed_log_fitness_ratio),
                mean_case_fitness=_ratio(value.whole_mean_trace_fitness_ratio),
                case_status_counts=dict(Counter(row.status for row in value.traces)),
                lowest_fitness_cases=[
                    {
                        "case_id": row.case_id,
                        "status": row.status,
                        "cost": row.alignment_cost,
                        "fitness": _ratio(row.fitness_ratio),
                    }
                    for row in worst
                ],
                truncated=truncated,
            )
            if include_deviations:
                aligned = align_traces(log, net, spec)
                if aligned.value is not None:
                    log_moves: Counter[str] = Counter()
                    model_moves: Counter[str] = Counter()
                    deviating = 0
                    for alignment in aligned.value.alignments:
                        visible = [
                            m for m in alignment.moves if m.kind in ("log", "model")
                        ]
                        deviating += bool(visible)
                        for move in visible:
                            target = log_moves if move.kind == "log" else model_moves
                            target[move.activity or "<unlabeled>"] += 1
                    payload["deviations"] = {
                        "cases_with_deviations": deviating,
                        "log_moves": dict(log_moves.most_common(limit)),
                        "model_moves": dict(model_moves.most_common(limit)),
                        "meaning": "log move: event in the log the model cannot "
                        "follow; model move: activity the model requires but the "
                        "log lacks",
                    }
            return payload
        if method == "token":
            result = measure_token_fitness(log, net)
            payload = _envelope(result, limit)
            value = result.value
            if value is None:
                return payload
            payload.update(
                method="token",
                requested_cases=value.requested_count,
                completed_cases=value.completed_count,
                limited_cases=value.limited_count,
                log_fitness=_ratio(value.whole_log_fitness_ratio),
                mean_case_fitness=_ratio(value.whole_mean_trace_fitness_ratio),
                fitting_case_ratio=_ratio(value.whole_fitting_trace_ratio),
                token_counts=_json(value.completed_counts),
            )
            return payload
        raise ToolError("invalid_argument", "method must be alignment or token")

    @_tool
    def export(
        self,
        handle: str,
        path: str,
        format: str | None = None,
        overwrite: bool = False,
    ) -> dict[str, object]:
        """Write a handle to disk: case log as XES, OCEL as JSON/XML/SQLite, model files."""
        entry = self._get(handle)
        destination = self._output_path(path, overwrite)
        if entry.kind == "case_log":
            from pix.event_log import write_xes

            if format not in (None, "xes"):
                raise ToolError("unsupported_format", "case logs export as xes")
            receipt = write_xes(entry.value, destination, overwrite=overwrite)
        elif entry.kind == "ocel":
            from pix.ocel import export_ocel

            receipt = export_ocel(
                entry.value, destination, format=format or "json", overwrite=overwrite
            )
        else:
            selected = format or destination.suffix.lstrip(".").lower()
            if selected == "pnml" and "net" in entry.value:
                from pix.model_io import write_pnml

                receipt = write_pnml(
                    entry.value["net"], destination, overwrite=overwrite
                )
            elif selected == "ptml" and "tree" in entry.value:
                from pix.model_io import write_ptml

                receipt = write_ptml(
                    entry.value["tree"], destination, overwrite=overwrite
                )
            elif selected == "json":
                from pix.models import write_model

                model = entry.value.get("tree") or entry.value.get("net")
                if model is None:
                    raise ToolError("unsupported_format", "no exportable model")
                receipt = write_model(model, destination, overwrite=overwrite)
            else:
                raise ToolError(
                    "unsupported_format",
                    "models export as pnml (Petri net), ptml (process tree) or json",
                )
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        return {
            "status": "computed",
            "handle": handle,
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "sha256": digest,
            "receipt": _compact(_json(receipt), 10),
        }

    @_tool
    def list_handles(self) -> dict[str, object]:
        """List open handles, oldest first (old handles are evicted past the cap)."""
        return {
            "status": "computed",
            "handles": [self._describe(entry) for entry in self._entries.values()],
            "max_handles": self.max_handles,
        }

    @_tool
    def release(self, handle: str) -> dict[str, object]:
        """Forget a handle and free its memory."""
        self._get(handle)
        del self._entries[handle]
        return {"status": "computed", "released": handle}


def _parse_time(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ToolError(
            "invalid_time", f"{name} must be ISO 8601: {value!r}"
        ) from error
    if parsed.utcoffset() is None:
        raise ToolError(
            "invalid_time", f"{name} needs a timezone, e.g. 2026-01-01T00:00:00Z"
        )
    return parsed


def _scalar(value: object, kind: str, scalar_type: type) -> object:
    fields_by_type = {
        "string": "text_value",
        "id": "text_value",
        "int": "int_value",
        "float": "float_value",
        "boolean": "bool_value",
        "date": "date_value",
    }
    if kind == "null":
        return scalar_type("null")
    if kind not in fields_by_type:
        raise ToolError(
            "invalid_argument",
            f"attribute_value_type must be one of {sorted([*fields_by_type, 'null'])}",
        )
    if kind == "date" and isinstance(value, str):
        value = _parse_time(value, "attribute value")
    elif kind == "float" and type(value) is int:
        value = float(value)
    return scalar_type(kind, **{fields_by_type[kind]: value})


_TREE_SYMBOLS = {"sequence": "->", "xor": "X", "parallel": "+", "loop": "*", "or": "O"}


def _tree_text(tree: object) -> str:
    operator = tree.operator
    if operator == "activity":
        return repr(tree.activity)
    if operator == "tau":
        return "tau"
    symbol = _TREE_SYMBOLS.get(operator, operator)
    return f"{symbol}(" + ", ".join(_tree_text(child) for child in tree.children) + ")"


__all__ = ["ADAPTER_VERSION", "FILTER_KINDS", "PixToolbox", "ToolError"]
