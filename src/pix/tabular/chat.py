"""Declarative conversation records to OCEL, preserving uncertainty and rule identity."""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import ClassVar, Literal

from pix.contracts.analysis import _text
from pix.contracts.result import _identity_value
from pix.contracts.time import TimePrecision, validate_precision
from pix.ocel import (
    E2O,
    OCEL,
    Attribute,
    Event,
    EventAttr,
    EventType,
    Object,
    ObjectType,
    ValueType,
    build,
)
from pix.ocel.ingest.contract import ImportIssue, ImportStage, ImportStatus


@dataclass(frozen=True, slots=True)
class MatchRule:
    label: str
    field: str
    op: Literal["equals", "prefix", "regex", "present"]
    value: str | None = None
    when: tuple[MatchRule, ...] = ()

    def __post_init__(self):
        _text(self.label, "label")
        _text(self.field, "field")
        if any(not part for part in self.field.split(".")):
            raise ValueError("field paths must have nonempty components")
        if self.op not in ("equals", "prefix", "regex", "present"):
            raise ValueError("unsupported match operation")
        if self.op != "present":
            _text(self.value, "value", blank=True)
        elif self.value is not None:
            raise ValueError("present rules do not accept a value")
        if self.op == "regex":
            re.compile(self.value)
        if not isinstance(self.when, tuple) or not all(
            isinstance(r, MatchRule) for r in self.when
        ):
            raise TypeError("when must be a tuple of MatchRule")


@dataclass(frozen=True, slots=True)
class CarrierRule:
    send: MatchRule
    receive: MatchRule
    receiver_field: str | None = None
    pair_key: Literal["explicit_id", "sender_receiver_order"] = "explicit_id"
    explicit_id_field: str | None = None
    object_type: str = "message"
    # Receiving author can be the sender; the receiving endpoint is explicit.
    receiving_actor_field: str = "conversation_id"

    def __post_init__(self):
        if not isinstance(self.send, MatchRule) or not isinstance(
            self.receive, MatchRule
        ):
            raise TypeError("carrier predicates must be MatchRule")
        if self.pair_key not in ("explicit_id", "sender_receiver_order"):
            raise ValueError("unsupported pair_key")
        if self.pair_key == "explicit_id" and self.explicit_id_field is None:
            raise ValueError("explicit_id pairing requires explicit_id_field")
        if self.pair_key == "sender_receiver_order" and self.receiver_field is None:
            raise ValueError("sender_receiver_order requires receiver_field")
        for name in (
            "receiver_field",
            "explicit_id_field",
            "receiving_actor_field",
            "object_type",
        ):
            if getattr(self, name) is not None:
                _text(getattr(self, name), name)
        _text(self.receiving_actor_field, "receiving_actor_field")
        if self.object_type in ("employee", "request", "channel"):
            raise ValueError(
                "carrier object_type must differ from actor, turn and channel types"
            )


@dataclass(frozen=True, slots=True)
class ChatLogMapping:
    SCHEMA_VERSION: ClassVar[str] = "1.0.0"
    conversation_key: str = "conversation_id"
    position_key: str = "position"
    author_key: str = "author"
    time_key: str = "sent_at"
    time_precision: TimePrecision | None = None
    turn_openers: tuple[MatchRule, ...] = ()
    activity_rules: tuple[MatchRule, ...] = ()
    unmatched_activity: Literal["error", "label_unclassified", "drop_with_count"] = (
        "label_unclassified"
    )
    anchor_policy: Literal["previous_observed", "reject"] = "previous_observed"
    carrier_rules: tuple[CarrierRule, ...] = ()
    object_id_namespace: bool = True
    retain_text: bool = False
    text_digest: Literal["sha256", "none"] = "sha256"
    max_records: int = 1_000_000

    def __post_init__(self):
        for name in ("conversation_key", "position_key", "author_key", "time_key"):
            _text(getattr(self, name), name)
        for name, kind in (
            ("turn_openers", MatchRule),
            ("activity_rules", MatchRule),
            ("carrier_rules", CarrierRule),
        ):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not all(
                isinstance(v, kind) for v in values
            ):
                raise TypeError(f"{name} must be a tuple of {kind.__name__}")
        if self.unmatched_activity not in (
            "error",
            "label_unclassified",
            "drop_with_count",
        ):
            raise ValueError("unsupported unmatched_activity")
        if self.anchor_policy not in ("previous_observed", "reject"):
            raise ValueError("unsupported anchor_policy")
        if self.text_digest not in ("sha256", "none"):
            raise ValueError("unsupported text_digest")
        if (
            type(self.object_id_namespace) is not bool
            or type(self.retain_text) is not bool
        ):
            raise TypeError("text retention and namespace flags must be bool")
        if type(self.max_records) is not int or self.max_records < 1:
            raise ValueError("max_records must be a positive integer")
        validate_precision(self.time_precision)


@dataclass(frozen=True, slots=True)
class ChatImportResult:
    status: ImportStatus
    candidate: OCEL | None
    import_issues: tuple[ImportIssue, ...]
    mapping_digest: str
    rule_hits: tuple[tuple[str, int], ...]
    unclassified_count: int
    anchored_count: int
    turn_count: int
    dropped_count: int = 0

    @property
    def valid(self):
        return self.status is ImportStatus.VALID


def _get(record, path):
    value = record
    for part in path.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def _matches(rule, record):
    value = _get(record, rule.field)
    match = (
        value is not None
        if rule.op == "present"
        else value == rule.value
        if rule.op == "equals"
        else isinstance(value, str)
        and (
            value.startswith(rule.value)
            if rule.op == "prefix"
            else re.search(rule.value, value) is not None
        )
    )
    return match and all(_matches(condition, record) for condition in rule.when)


def _digest(value):
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _timestamp(value):
    if value is None:
        return None
    if isinstance(value, str):
        # datetime.fromisoformat truncates fractional digits; reject loss explicitly.
        if re.search(r"[.,]\d{6}[1-9]|[.,]\d{6}\d*[1-9]", value):
            raise ValueError("timestamp_precision_loss")
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("timezone_aware_timestamp_required")
    return value.astimezone(timezone.utc)


def import_chat_log(
    source: str | os.PathLike | Iterable[Mapping[str, object]], mapping: ChatLogMapping
) -> ChatImportResult:
    """Import JSONL or records using source positions, never fabricated µs order.

    Matching is first-rule-wins. An opener label is the activity fallback.
    Records before any opener follow the unmatched policy; label mode creates an
    explicit unclassified turn. A trailing anchor has no finite upper bound.
    Order pairing is a declared sender/receiver sequence convention, not proof
    that two messages are the same; prefer source explicit IDs when available.
    """
    if not isinstance(mapping, ChatLogMapping):
        raise TypeError("mapping must be ChatLogMapping")
    digest = "pix.chat-mapping.v1:sha256:" + _digest(_identity_value(mapping))
    hits = Counter()
    unclassified = anchored = turns = dropped = 0

    def result(status, candidate=None, issues=()):
        return ChatImportResult(
            status,
            candidate,
            issues,
            digest,
            tuple(sorted(hits.items())),
            unclassified,
            anchored,
            turns,
            dropped,
        )

    def failure(code, status=ImportStatus.MAPPING_INVALID, stage=ImportStage.MAPPING):
        return result(
            status, issues=(ImportIssue(stage, code, "Chat import failed: " + code),)
        )

    rows = []
    try:
        if isinstance(source, (str, os.PathLike)):
            with Path(source).open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        rows.append(json.loads(line))
                        if len(rows) > mapping.max_records:
                            return failure("chat_record_limit_exceeded")
        else:
            for row in source:
                rows.append(row)
                if len(rows) > mapping.max_records:
                    return failure("chat_record_limit_exceeded")
    except (OSError, UnicodeError):
        return failure(
            "chat_source_unavailable", ImportStatus.UNAVAILABLE, ImportStage.SOURCE
        )
    except (json.JSONDecodeError, TypeError):
        return failure(
            "invalid_chat_jsonl", ImportStatus.SYNTAX_INVALID, ImportStage.SYNTAX
        )

    objects, events, relations, prepared = {}, [], set(), []
    schemas = defaultdict(dict)

    def object_id(kind, raw):
        _text(raw, "object ID")
        oid = f"{kind}:{raw}" if mapping.object_id_namespace else raw
        if oid in objects and objects[oid].type != kind:
            raise ValueError("conflicting_object_type")
        objects[oid] = Object(oid, kind)
        return oid

    def relate(eid, kind, raw, qualifier):
        oid = object_id(kind, raw)
        relations.add(E2O(eid, oid, qualifier))
        return oid

    try:
        conversations = defaultdict(list)
        identities = set()
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("chat_record_must_be_mapping")
            conversation = _get(row, mapping.conversation_key)
            author = _get(row, mapping.author_key)
            position = _get(row, mapping.position_key)
            _text(conversation, "conversation")
            _text(author, "author")
            if type(position) is not int or position < 0:
                raise ValueError("invalid_chat_position")
            if (conversation, position) in identities:
                raise ValueError("duplicate_chat_position")
            identities.add((conversation, position))
            conversations[conversation].append(
                (position, row, _timestamp(_get(row, mapping.time_key)))
            )
        for conversation, records in sorted(conversations.items()):
            records.sort(key=lambda r: r[0])
            upper_bounds = {}
            next_observed = None
            for position, row, time in reversed(records):
                upper_bounds[position] = next_observed
                if time is not None:
                    next_observed = time
            previous_observed = turn = trigger = None
            turn_number = 0
            for position, row, observed in records:
                if observed is not None:
                    if previous_observed is not None and observed < previous_observed:
                        raise ValueError("chat_observed_time_reversal")
                    previous_observed = observed
                opener = next(
                    (r for r in mapping.turn_openers if _matches(r, row)), None
                )
                activity_rule = next(
                    (r for r in mapping.activity_rules if _matches(r, row)), None
                )
                if opener:
                    hits[opener.label] += 1
                if activity_rule:
                    hits[activity_rule.label] += 1
                activity = (
                    activity_rule.label
                    if activity_rule
                    else opener.label
                    if opener
                    else None
                )
                unmatched = activity is None or (turn is None and opener is None)
                if unmatched:
                    unclassified += 1
                    if mapping.unmatched_activity == "error":
                        raise ValueError("unclassified_chat_record")
                    if mapping.unmatched_activity == "drop_with_count":
                        dropped += 1
                        continue
                    activity = "unclassified"
                if opener or turn is None:
                    turn_number += 1
                    turns += 1
                    trigger = opener.label if opener else "unclassified"
                    turn = _digest([conversation, turn_number])
                if observed is None and (
                    mapping.anchor_policy == "reject" or previous_observed is None
                ):
                    raise ValueError("chat_timestamp_unanchorable")
                time = observed if observed is not None else previous_observed
                eid = "chat:" + _digest([conversation, position])
                attrs = {
                    "position": position,
                    "trigger": trigger,
                    "pix:chat_mapping_digest": digest,
                    "time_basis": "observed"
                    if observed is not None
                    else "anchor_previous_observed",
                }
                if mapping.time_precision is not None:
                    value = (
                        mapping.time_precision.granularity_microseconds
                        if mapping.time_precision.attribute is None
                        else _get(row, mapping.time_precision.attribute)
                    )
                    if type(value) is not int or value < 1:
                        raise ValueError("invalid_chat_time_precision")
                    attrs["time_granularity_microseconds"] = value
                    if mapping.time_precision.attribute is not None:
                        key = mapping.time_precision.attribute
                        if key in attrs or key in (
                            "time_lower",
                            "time_upper",
                            "text",
                            "text_sha256",
                        ):
                            raise ValueError("precision_attribute_conflict")
                        attrs[key] = value
                if observed is None:
                    anchored += 1
                    attrs["time_lower"] = time
                    if upper_bounds[position] is not None:
                        attrs["time_upper"] = upper_bounds[position]
                text = row.get("text")
                if text is not None:
                    if not isinstance(text, str):
                        raise ValueError("chat_text_must_be_string")
                    if mapping.retain_text:
                        attrs["text"] = text
                    if mapping.text_digest == "sha256":
                        attrs["text_sha256"] = sha256(text.encode()).hexdigest()
                for name, value in attrs.items():
                    schemas[activity][name] = (
                        ValueType.TIME
                        if isinstance(value, datetime)
                        else ValueType.INTEGER
                        if type(value) is int
                        else ValueType.STRING
                    )
                events.append(
                    Event(
                        eid,
                        activity,
                        time,
                        tuple(EventAttr(k, v) for k, v in sorted(attrs.items())),
                    )
                )
                relate(eid, "employee", _get(row, mapping.author_key), "actor")
                relate(eid, "channel", conversation, "room")
                relate(eid, "request", turn, "request")
                prepared.append((conversation, position, eid, row))

        for rule_index, rule in enumerate(mapping.carrier_rules):
            send_order, receive_order = Counter(), Counter()
            seen_explicit = set()
            pair_conversations = defaultdict(set)
            for conversation, position, eid, row in prepared:
                send, receive = _matches(rule.send, row), _matches(rule.receive, row)
                if send and receive:
                    raise ValueError("mixed_chat_carrier_roles")
                if not send and not receive:
                    continue
                hits[(rule.send if send else rule.receive).label] += 1
                author = _get(row, mapping.author_key)
                receiver = (
                    _get(row, rule.receiver_field)
                    if send and rule.receiver_field
                    else _get(row, rule.receiving_actor_field)
                    if receive
                    else None
                )
                if receiver is not None:
                    _text(receiver, "receiver")
                    relate(eid, "employee", receiver, "receiver")
                if rule.pair_key == "explicit_id":
                    key = _get(row, rule.explicit_id_field)
                    _text(key, "explicit carrier ID")
                    # Repeated receives allow broadcast, duplicate sends are ambiguous.
                    if send and key in seen_explicit:
                        raise ValueError("duplicate_chat_carrier_send")
                    if send:
                        seen_explicit.add(key)
                    identity = [rule_index, key]
                else:
                    if receiver is None:
                        raise ValueError("missing_chat_receiver")
                    pair = author, receiver
                    pair_conversations[send, pair].add(conversation)
                    if len(pair_conversations[send, pair]) > 1:
                        raise ValueError("ambiguous_chat_pair_order")
                    counts = send_order if send else receive_order
                    counts[pair] += 1
                    identity = [rule_index, author, receiver, counts[pair]]
                relate(
                    eid,
                    rule.object_type,
                    _digest(identity),
                    "sent" if send else "received",
                )
    except (ValueError, TypeError, OverflowError) as exc:
        # Do not echo record contents (including malformed text/time values).
        safe_codes = {
            "ambiguous_chat_pair_order",
            "precision_attribute_conflict",
            "conflicting_object_type",
            "chat_record_must_be_mapping",
            "invalid_chat_position",
            "duplicate_chat_position",
            "chat_observed_time_reversal",
            "unclassified_chat_record",
            "chat_timestamp_unanchorable",
            "invalid_chat_time_precision",
            "chat_text_must_be_string",
            "mixed_chat_carrier_roles",
            "duplicate_chat_carrier_send",
            "missing_chat_receiver",
            "timestamp_precision_loss",
            "timezone_aware_timestamp_required",
        }
        return failure(str(exc) if str(exc) in safe_codes else "invalid_chat_record")
    built = build(
        event_types=tuple(
            EventType(name, tuple(Attribute(k, v) for k, v in sorted(attrs.items())))
            for name, attrs in sorted(schemas.items())
        ),
        object_types=tuple(
            ObjectType(t)
            for t in sorted(
                {
                    "employee",
                    "request",
                    "channel",
                    *(r.object_type for r in mapping.carrier_rules),
                }
            )
        ),
        events=tuple(events),
        objects=tuple(objects.values()),
        e2o=tuple(relations),
    )
    if built.ocel is None:
        return failure(
            "invalid_chat_ocel", ImportStatus.SEMANTIC_INVALID, ImportStage.SEMANTIC
        )
    return result(ImportStatus.VALID, built.ocel)


__all__ = [
    "MatchRule",
    "CarrierRule",
    "ChatLogMapping",
    "ChatImportResult",
    "import_chat_log",
]
