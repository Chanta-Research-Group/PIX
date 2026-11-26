"""Shared synthetic case table for the MCP adapter tests."""

from pathlib import Path

import pytest

ROWS = (
    ("1", "A", "2026-01-01T09:00:00Z", "u1"),
    ("1", "B", "2026-01-01T10:00:00Z", "u2"),
    ("1", "C", "2026-01-01T11:00:00Z", "u1"),
    ("2", "A", "2026-01-02T09:00:00Z", "u1"),
    ("2", "X", "2026-01-02T09:30:00Z", "u3"),
    ("2", "C", "2026-01-02T12:00:00Z", "u2"),
    ("3", "A", "2026-01-03T09:00:00Z", "u2"),
    ("3", "C", "2026-01-03T09:10:00Z", "u2"),
    ("4", "X", "2026-01-04T09:00:00Z", "u1"),
    ("4", "A", "2026-01-04T10:00:00Z", "u1"),
    ("4", "C", "2026-01-04T11:00:00Z", "u3"),
    ("5", "A", "2026-01-05T09:00:00Z", "u1"),
    ("5", "C", "2026-01-05T10:00:00Z", "u1"),
    ("5", "D", "2026-01-05T11:00:00Z", "u2"),
)


def write_table(directory: Path) -> Path:
    path = directory / "log.csv"
    lines = ["case,activity,time,resource", *(",".join(row) for row in ROWS)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def table_dir(tmp_path: Path) -> Path:
    write_table(tmp_path)
    return tmp_path
