"""Issue #11's eight-record example and cross-operator provenance/uncertainty."""

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from pix.api import (
    CarrierRule,
    ChatLogMapping,
    HandoverSpec,
    MatchRule,
    TimePrecision,
    TraceSpec,
    discover_handover,
    import_chat_log,
    reconstruct_traces,
    result_from_json,
    result_json_bytes,
)
from pix.ocel import canonical_digest
from pix.ocel.canonical import canonical_bytes

ROWS = [
    dict(
        conversation_id="agent_A",
        position=1,
        author_kind="user",
        author="user_1",
        sent_at="2026-01-05T09:00+09:00",
        text="private user sentence",
    ),
    dict(
        conversation_id="agent_A",
        position=2,
        author_kind="agent",
        author="agent_A",
        sent_at=None,
        tool="send_to_agent",
        tool_args={"to": "agent_B"},
        text="private tool sentence",
    ),
    dict(
        conversation_id="agent_A",
        position=3,
        author_kind="agent",
        author="agent_A",
        sent_at=None,
        tool="send_to_user",
        text="private response sentence",
    ),
    dict(
        conversation_id="agent_A",
        position=4,
        author_kind="system",
        author="runtime",
        sent_at=None,
        text="[routine] 'daily digest' failed",
    ),
    dict(
        conversation_id="agent_A",
        position=5,
        author_kind="system",
        author="runtime",
        sent_at="2026-01-05T09:30+09:00",
        text="[system] reminder: report needed",
    ),
    dict(
        conversation_id="agent_B",
        position=1,
        author_kind="agent_message",
        author="agent_A",
        sent_at="2026-01-05T09:01+09:00",
        text="[agent] private request sentence",
    ),
    dict(
        conversation_id="agent_B",
        position=2,
        author_kind="agent",
        author="agent_B",
        sent_at=None,
        tool="write_file",
        text="private write sentence",
    ),
    dict(
        conversation_id="agent_B",
        position=3,
        author_kind="agent",
        author="agent_B",
        sent_at=None,
        tool="send_to_agent",
        tool_args={"to": "agent_A"},
        text="private reply sentence",
    ),
]


def mapping():
    return ChatLogMapping(
        time_precision=TimePrecision(60_000_000),
        turn_openers=(
            MatchRule("user_request_received", "author_kind", "equals", "user"),
            MatchRule("routine_failed", "text", "prefix", "[routine]"),
            MatchRule("system_reprompt", "text", "prefix", "[system] reminder"),
            MatchRule(
                "agent_request_received", "author_kind", "equals", "agent_message"
            ),
        ),
        activity_rules=(
            MatchRule("handoff_sent", "tool", "equals", "send_to_agent"),
            MatchRule("reported", "tool", "equals", "send_to_user"),
            MatchRule("doc_written", "tool", "equals", "write_file"),
        ),
        carrier_rules=(
            CarrierRule(
                MatchRule("send", "tool", "equals", "send_to_agent"),
                MatchRule("receive", "author_kind", "equals", "agent_message"),
                receiver_field="tool_args.to",
                pair_key="sender_receiver_order",
            ),
        ),
    )


def test_turn_split_and_trigger_rules(tmp_path):
    path = tmp_path / "chat.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in ROWS))
    result = import_chat_log(path, mapping())
    assert result.valid, result.import_issues
    assert result.turn_count == 4
    assert result.anchored_count == 5
    assert result.unclassified_count == result.dropped_count == 0
    assert len(result.candidate.events_by_type("handoff_sent")) == 2
    assert len(result.candidate.objects_by_type("message")) == 2
    handover = discover_handover(
        result.candidate, HandoverSpec(time_precision=TimePrecision(60_000_000))
    )
    assert handover.status.value == "computed", handover.issues
    assert len(handover.value.links) == 1
    link = handover.value.links[0]
    assert (link.sender, link.receiver) == ("employee:agent_A", "employee:agent_B")
    assert len(handover.value.unmatched_sends) == 1
    assert len(handover.value.unmatched_receives) == 0


def test_anchor_bounds_without_invented_microseconds():
    result = import_chat_log(ROWS, mapping())
    failure = result.candidate.events_by_type("routine_failed")[0]
    attrs = {a.name: a.value for a in failure.attributes}
    assert attrs["time_basis"] == "anchor_previous_observed"
    assert (
        failure.time
        == attrs["time_lower"]
        == datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc)
    )
    assert attrs["time_upper"] == datetime(2026, 1, 5, 0, 30, tzinfo=timezone.utc)
    assert all(e.time.microsecond == 0 for e in result.candidate.events)
    trailing = result.candidate.events_by_type("doc_written")[0]
    assert "time_upper" not in {a.name for a in trailing.attributes}
    traces = reconstruct_traces(
        result.candidate,
        TraceSpec(
            "request", tie_policy="concurrent", time_precision=TimePrecision(60_000_000)
        ),
    )
    assert traces.status.value == "computed"


def test_text_not_retained_by_default():
    result = import_chat_log(ROWS, mapping())
    serialized = canonical_bytes(result.candidate).decode()
    assert all(row["text"] not in serialized for row in ROWS)
    assert "text_sha256" in serialized
    result = import_chat_log(ROWS, replace(mapping(), text_digest="none"))
    assert "text_sha256" not in canonical_bytes(result.candidate).decode()
    result = import_chat_log(ROWS, replace(mapping(), retain_text=True))
    assert ROWS[0]["text"] in canonical_bytes(result.candidate).decode()


def test_mapping_digest_in_provenance_and_determinism():
    first = import_chat_log(ROWS, mapping())
    again = import_chat_log(reversed(ROWS), mapping())
    assert first.mapping_digest == again.mapping_digest
    assert canonical_digest(first.candidate) == canonical_digest(again.candidate)
    changed = import_chat_log(
        ROWS,
        replace(
            mapping(),
            activity_rules=mapping().activity_rules
            + (MatchRule("unused", "tool", "equals", "never"),),
        ),
    )
    assert first.mapping_digest != changed.mapping_digest
    assert canonical_digest(first.candidate) != canonical_digest(changed.candidate)
    for result in (
        reconstruct_traces(
            first.candidate,
            TraceSpec(
                "message",
                tie_policy="concurrent",
                time_precision=TimePrecision(60_000_000),
            ),
        ),
        discover_handover(first.candidate, HandoverSpec()),
    ):
        assert ("mapping_digest", first.mapping_digest) in {
            i.at for i in result.issues if i.code == "source_mapping_digest"
        }
        assert result_from_json(result_json_bytes(result)) == result


def test_namespace_avoids_id_conflict():
    row = dict(ROWS[0], author="agent_A")
    assert import_chat_log([row], mapping()).valid
    result = import_chat_log([row], replace(mapping(), object_id_namespace=False))
    assert result.status.value == "mapping_invalid"
    assert result.import_issues[0].code == "conflicting_object_type"


@pytest.mark.parametrize(
    "policy,expected",
    [
        ("error", "mapping_invalid"),
        ("drop_with_count", "valid"),
        ("label_unclassified", "valid"),
    ],
)
def test_unmatched_policies_and_counts(policy, expected):
    row = dict(ROWS[0], author_kind="unknown")
    result = import_chat_log([row], replace(mapping(), unmatched_activity=policy))
    assert result.status.value == expected
    assert result.unclassified_count == 1
    if policy == "drop_with_count":
        assert result.dropped_count == 1
        assert not result.candidate.events
    if policy == "label_unclassified":
        assert result.turn_count == 1
        assert result.candidate.events[0].type == "unclassified"


@pytest.mark.parametrize(
    "change,code",
    [
        ({"position": True}, "invalid_chat_position"),
        ({"sent_at": None}, "chat_timestamp_unanchorable"),
        ({"sent_at": "2026-01-01T00:00"}, "timezone_aware_timestamp_required"),
        ({"sent_at": "2026-01-01T00:00:00.1234567Z"}, "timestamp_precision_loss"),
    ],
)
def test_invalid_records_fail_without_source_text(change, code):
    result = import_chat_log([dict(ROWS[0], **change)], mapping())
    assert result.status.value == "mapping_invalid"
    assert result.candidate is None
    assert result.import_issues[0].code == code
    assert ROWS[0]["text"] not in repr(result)


def test_duplicate_positions_and_record_limit():
    assert (
        import_chat_log([ROWS[0], ROWS[0]], mapping()).import_issues[0].code
        == "duplicate_chat_position"
    )
    assert (
        import_chat_log(ROWS, replace(mapping(), max_records=1)).import_issues[0].code
        == "chat_record_limit_exceeded"
    )


def test_explicit_carrier_ids_and_nested_rule_conditions():
    rows = [
        dict(
            ROWS[0], message_id="m", tool="send_to_agent", tool_args={"to": "agent_B"}
        ),
        dict(ROWS[5], message_id="m"),
    ]
    rule = replace(
        mapping().carrier_rules[0],
        pair_key="explicit_id",
        explicit_id_field="message_id",
    )
    result = import_chat_log(rows, replace(mapping(), carrier_rules=(rule,)))
    assert result.valid
    assert len(result.candidate.objects_by_type("message")) == 1
    conditional = MatchRule(
        "report",
        "tool",
        "regex",
        "send_.*",
        (MatchRule("has_receiver", "tool_args.to", "present"),),
    )
    result = import_chat_log(
        rows, replace(mapping(), activity_rules=(conditional,), carrier_rules=(rule,))
    )
    assert result.valid
    assert len(result.candidate.events_by_type("report")) == 1


def test_anchor_bounds_are_not_lost_without_precision_option():
    imported = import_chat_log(ROWS, replace(mapping(), time_precision=None))
    result = discover_handover(imported.candidate, HandoverSpec())
    link = result.value.links[0]
    assert link.latency_lower_microseconds == -29 * 60 * 1_000_000
    assert link.latency_upper_microseconds == 60 * 1_000_000
    traces = reconstruct_traces(
        imported.candidate, TraceSpec("request", tie_policy="concurrent")
    )
    assert any(
        e.time_lower is not None for trace in traces.value.traces for e in trace.events
    )


def test_per_record_precision_is_retained_under_selected_name():
    imported = import_chat_log(
        [dict(ROWS[0], resolution=60_000_000)],
        replace(mapping(), time_precision=TimePrecision(attribute="resolution")),
    )
    assert imported.valid
    result = reconstruct_traces(
        imported.candidate,
        TraceSpec("request", time_precision=TimePrecision(attribute="resolution")),
    )
    assert result.status.value == "computed"
