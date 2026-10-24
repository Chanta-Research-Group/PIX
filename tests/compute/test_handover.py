"""Issue #10: joins use carrier identity rather than ordering of events."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from pix.api import (
    HandoverSpec,
    TimePrecision,
    discover_handover,
    result_from_json,
    result_json_bytes,
)
from pix.ocel import (
    E2O,
    OCEL,
    Attribute,
    Event,
    EventType,
    Object,
    ObjectAttr,
    ObjectType,
    ValueType,
)

T = datetime(2026, 1, 5, tzinfo=timezone.utc)


def log():
    events, relations = [], []
    for i, (sender, receiver) in enumerate((("A", "B"), ("A", "C"), ("B", "C"))):
        events.extend((Event(f"s{i}", "send", T), Event(f"r{i}", "receive", T)))
        relations.extend(
            (
                E2O(f"s{i}", f"m{i}", "sent"),
                E2O(f"s{i}", sender, "actor"),
                E2O(f"r{i}", f"m{i}", "received"),
                E2O(f"r{i}", receiver, "actor"),
            )
        )
    return OCEL(
        (EventType("send"), EventType("receive")),
        (
            ObjectType("message"),
            ObjectType("employee", (Attribute("team", ValueType.STRING),)),
        ),
        tuple(events),
        tuple(Object(f"m{i}", "message") for i in range(3))
        + tuple(
            Object(a, "employee", (ObjectAttr("team", "T1" if a == "A" else "T2", T),))
            for a in "ABC"
        ),
        tuple(relations),
    )


def test_carrier_links_independent_of_tie_order():
    result = discover_handover(log(), HandoverSpec())
    assert result.status.value == "computed"
    assert {(e.sender, e.receiver, e.link_count) for e in result.value.edges} == {
        ("A", "B", 1),
        ("A", "C", 1),
        ("B", "C", 1),
    }
    assert not result.value.unmatched_sends and not result.value.unmatched_receives
    assert all(
        len(link.send_relations) == len(link.receive_relations) == 2
        for link in result.value.links
    )
    reordered = replace(
        log(), events=tuple(reversed(log().events)), e2o=tuple(reversed(log().e2o))
    )
    assert discover_handover(reordered, HandoverSpec()) == result
    assert result_from_json(result_json_bytes(result)) == result


def test_early_receive_link_retained_and_precision_respected():
    source = log()
    source = replace(
        source,
        events=tuple(
            replace(e, time=T - timedelta(seconds=30)) if e.id == "r0" else e
            for e in source.events
        ),
    )
    result = discover_handover(source, HandoverSpec())
    assert len(result.value.links) == 3
    assert result.value.order_conflicts == (("s0", "r0"),)
    result = discover_handover(
        source, HandoverSpec(time_precision=TimePrecision(60_000_000))
    )
    assert not result.value.order_conflicts


def test_unmatched_sends_reported_not_partial():
    source = log()
    source = replace(
        source,
        e2o=tuple(
            r for r in source.e2o if not (r.event == "r0" and r.qualifier == "received")
        ),
    )
    result = discover_handover(source, HandoverSpec())
    assert result.status.value == "computed"
    assert result.value.unmatched_sends == ("s0",)
    assert "unmatched_handover_events" in {i.code for i in result.issues}


def test_multi_receiver_each_and_reject():
    source = log()
    source = replace(source, e2o=source.e2o + (E2O("r0", "C", "actor"),))
    assert len(discover_handover(source, HandoverSpec()).value.links) == 4
    assert (
        discover_handover(source, HandoverSpec(multi_receiver="reject")).status.value
        == "invalid_input"
    )


def test_event_roles_without_receive_and_self_exclusion():
    source = log()
    source = replace(source, e2o=(E2O("s0", "A", "sender"), E2O("s0", "B", "receiver")))
    result = discover_handover(source, HandoverSpec(mode="event_roles"))
    assert len(result.value.links) == 1
    assert result.value.links[0].receive_event_id is None
    assert result.value.links[0].latency_lower_microseconds is None
    source = replace(source, e2o=(E2O("s0", "A", "actor"),))
    result = discover_handover(source, HandoverSpec(mode="event_roles"))
    assert not result.value.links
    assert "self_handover_excluded" in {i.code for i in result.issues}


def test_group_edges_sum_and_link_limit():
    result = discover_handover(log(), HandoverSpec(group_by_object_attribute="team"))
    assert (
        sum(e.link_count for e in result.value.group_edges)
        == sum(e.link_count for e in result.value.edges)
        == 3
    )
    assert (
        discover_handover(log(), HandoverSpec(max_links=2)).status.value
        == "invalid_input"
    )


def test_mixed_carrier_roles_rejected():
    source = replace(log(), e2o=log().e2o + (E2O("s0", "m1", "received"),))
    assert discover_handover(source, HandoverSpec()).status.value == "invalid_input"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_links": True},
        {"mode": "guess"},
        {"send_qualifiers": ["sent"]},
        {"send_qualifiers": ("received",)},
    ],
)
def test_invalid_spec(kwargs):
    with pytest.raises((TypeError, ValueError)):
        HandoverSpec(**kwargs)
