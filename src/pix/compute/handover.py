"""Join qualified carrier identities across object traces, without time-order joins."""

from collections import defaultdict

from pix.compute._common import _prepare, _result
from pix.compute._time import elapsed, interval
from pix.compute.context import ComputationContext
from pix.contracts.analysis import E2OEvidence
from pix.contracts.handover import (
    HandoverEdge,
    HandoverLink,
    HandoverNetwork,
    HandoverSpec,
)
from pix.contracts.result import ComputationResult, ComputeIssue, ComputeStatus
from pix.ocel import OCEL

OPERATOR_ID = "pix.discover_handover"


def _edges(links, grouping=None):
    buckets = defaultdict(list)
    for link in links:
        key = (link.sender, link.receiver)
        if grouping is not None:
            key = grouping[link.sender], grouping[link.receiver]
        buckets[key].append(link)
    return tuple(
        HandoverEdge(
            sender,
            receiver,
            len(items),
            len(
                {i.carrier_object_id for i in items if i.carrier_object_id is not None}
            ),
            sum(
                i.latency_lower_microseconds is not None
                and i.latency_upper_microseconds is not None
                for i in items
            ),
            min(
                (
                    i.latency_lower_microseconds
                    for i in items
                    if i.latency_lower_microseconds is not None
                ),
                default=None,
            )
            if all(i.latency_lower_microseconds is not None for i in items)
            else None,
            max(
                (
                    i.latency_upper_microseconds
                    for i in items
                    if i.latency_upper_microseconds is not None
                ),
                default=None,
            )
            if all(i.latency_upper_microseconds is not None for i in items)
            else None,
        )
        for (sender, receiver), items in sorted(buckets.items())
    )


def discover_handover(
    log: OCEL | ComputationContext, spec: HandoverSpec
) -> ComputationResult[HandoverNetwork]:
    """Count carrier joins or co-observed event roles, retaining qualified evidence.

    Multiple sends/receives sharing a carrier produce all observed combinations.
    No causal order or missing recipient is inferred. Grouping requires a single
    stable string attribute per participating actor; dynamic membership is not
    silently resolved to a snapshot. A link limit rejects the whole request.
    """
    if not isinstance(spec, HandoverSpec):
        raise TypeError("spec must be HandoverSpec")
    context, issues = _prepare(log)

    def result(status, value=None, issues=()):
        return _result(OPERATOR_ID, context, spec, status, value, issues)

    if context is None:
        return result(ComputeStatus.INVALID_INPUT, issues=issues)
    required = (spec.actor_object_type,) + (
        (spec.carrier_object_type,) if spec.mode == "carrier_object" else ()
    )
    if any(t not in context.objects_by_type for t in required):
        return result(
            ComputeStatus.INVALID_INPUT,
            issues=(
                ComputeIssue(
                    "unknown_object_type", "Selected actor/carrier type is not declared"
                ),
            ),
        )

    def relations(eid, kind, qualifiers):
        found = tuple(
            E2OEvidence(r.event, r.object, r.qualifier)
            for r in context.e2o_by_event[eid]
            if context.objects_by_id[r.object].type == kind
            and r.qualifier in qualifiers
        )
        if kind == spec.actor_object_type and spec.mode == "carrier_object":
            shared = set(spec.sender_qualifiers) & set(spec.receiver_qualifiers)
            explicit = tuple(r for r in found if r.qualifier not in shared)
            if explicit:
                return explicit
        return found

    links = []
    sends, receives = set(), set()
    unmatched_sends, unmatched_receives, conflicts = set(), set(), set()
    actors, excluded = set(), 0
    problems = []

    def add(carrier, sid, rid, sr, rr):
        nonlocal excluded
        sender_ids = sorted(
            {
                r.object
                for r in sr
                if context.objects_by_id[r.object].type == spec.actor_object_type
            }
        )
        receiver_ids = sorted(
            {
                r.object
                for r in rr
                if context.objects_by_id[r.object].type == spec.actor_object_type
            }
        )
        actors.update(sender_ids + receiver_ids)
        if not sender_ids or not receiver_ids:
            raise ValueError("missing_handover_actor")
        if spec.multi_receiver == "reject" and len(receiver_ids) > 1:
            raise ValueError("multiple_handover_receivers")
        lo = hi = None
        if rid is not None:
            lo, hi = elapsed(
                interval(context.events_by_id[sid], spec.time_precision),
                interval(context.events_by_id[rid], spec.time_precision),
            )
            if hi is not None and hi < 0:
                conflicts.add((sid, rid))
        for sender in sender_ids:
            for receiver in receiver_ids:
                if not spec.include_self and sender == receiver:
                    excluded += 1
                    continue
                if len(links) >= spec.max_links:
                    raise ValueError("handover_link_limit_exceeded")
                links.append(
                    HandoverLink(
                        carrier,
                        sid,
                        rid,
                        sender,
                        receiver,
                        tuple(r for r in sr if r.object in (carrier, sender)),
                        tuple(r for r in rr if r.object in (carrier, receiver)),
                        lo,
                        hi,
                    )
                )

    try:
        if spec.mode == "event_roles":
            for event in context.log.events:
                sr = relations(event.id, spec.actor_object_type, spec.sender_qualifiers)
                rr = relations(
                    event.id, spec.actor_object_type, spec.receiver_qualifiers
                )
                actors.update(r.object for r in sr + rr)
                if sr:
                    sends.add(event.id)
                if rr:
                    receives.add(event.id)
                if sr and rr:
                    add(None, event.id, None, sr, rr)
                elif sr:
                    unmatched_sends.add(event.id)
                elif rr:
                    unmatched_receives.add(event.id)
        else:
            carrier_sends, carrier_receives = defaultdict(dict), defaultdict(dict)
            for event in context.log.events:
                sc = relations(event.id, spec.carrier_object_type, spec.send_qualifiers)
                rc = relations(
                    event.id, spec.carrier_object_type, spec.receive_qualifiers
                )
                if sc and rc:
                    raise ValueError("mixed_handover_event_roles")
                for selected, buckets, qualifiers, ids in (
                    (sc, carrier_sends, spec.sender_qualifiers, sends),
                    (rc, carrier_receives, spec.receiver_qualifiers, receives),
                ):
                    if not selected:
                        continue
                    ar = relations(event.id, spec.actor_object_type, qualifiers)
                    if not ar:
                        raise ValueError("missing_handover_actor")
                    actors.update(r.object for r in ar)
                    ids.add(event.id)
                    for carrier in sorted({r.object for r in selected}):
                        buckets[carrier][event.id] = ar + tuple(
                            r for r in selected if r.object == carrier
                        )
            for carrier in sorted(set(carrier_sends) | set(carrier_receives)):
                ss, rs = carrier_sends[carrier], carrier_receives[carrier]
                if not rs:
                    unmatched_sends.update(ss)
                if not ss:
                    unmatched_receives.update(rs)
                receivers = {
                    r.object
                    for evidence in rs.values()
                    for r in evidence
                    if context.objects_by_id[r.object].type == spec.actor_object_type
                }
                if spec.multi_receiver == "reject" and len(receivers) > 1:
                    raise ValueError("multiple_handover_receivers")
                for sid, sr in sorted(ss.items()):
                    for rid, rr in sorted(rs.items()):
                        add(carrier, sid, rid, sr, rr)
        grouping = None
        if spec.group_by_object_attribute is not None:
            grouping = {}
            for actor in actors:
                values = {
                    a.value
                    for a in context.objects_by_id[actor].attributes
                    if a.name == spec.group_by_object_attribute
                }
                if len(values) != 1 or not all(
                    isinstance(v, str) and v.strip() for v in values
                ):
                    raise ValueError("missing_or_dynamic_handover_group")
                grouping[actor] = next(iter(values))
    except (ValueError, TypeError, OverflowError) as exc:
        code = (
            str(exc)
            if str(exc)
            in {
                "missing_handover_actor",
                "multiple_handover_receivers",
                "handover_link_limit_exceeded",
                "mixed_handover_event_roles",
                "missing_or_dynamic_handover_group",
            }
            else "invalid_time_precision"
        )
        return result(
            ComputeStatus.INVALID_INPUT, issues=(ComputeIssue(code, str(exc)),)
        )
    if unmatched_sends or unmatched_receives:
        problems.append(
            ComputeIssue(
                "unmatched_handover_events",
                f"{len(unmatched_sends)} sends and {len(unmatched_receives)} receives lack a carrier counterpart",
            )
        )
    if conflicts:
        problems.append(
            ComputeIssue(
                "handover_order_conflicts",
                "Some receives precede sends beyond observation precision; links retained",
            )
        )
    if excluded:
        problems.append(
            ComputeIssue("self_handover_excluded", f"{excluded} self links excluded")
        )
    if any(
        link.receive_event_id is not None
        and (
            link.latency_lower_microseconds is None
            or link.latency_upper_microseconds is None
        )
        for link in links
    ):
        problems.append(
            ComputeIssue(
                "unbounded_handover_latency",
                "Some observed anchors lack finite latency bounds",
            )
        )
    links = tuple(
        sorted(
            links,
            key=lambda link: (
                link.carrier_object_id or "",
                link.send_event_id,
                link.receive_event_id or "",
                link.sender,
                link.receiver,
            ),
        )
    )
    return result(
        ComputeStatus.COMPUTED,
        HandoverNetwork(
            tuple(sorted(actors)),
            _edges(links),
            links,
            _edges(links, grouping) if grouping is not None else (),
            len(sends),
            len(receives),
            tuple(sorted(unmatched_sends)),
            tuple(sorted(unmatched_receives)),
            tuple(sorted(conflicts)),
        ),
        tuple(problems),
    )
