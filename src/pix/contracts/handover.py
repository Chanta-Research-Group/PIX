"""Qualified OCEL handover network contracts."""

from dataclasses import dataclass
from typing import ClassVar, Literal

from pix.contracts.analysis import E2OEvidence, _text
from pix.contracts.time import TimePrecision, validate_precision


@dataclass(frozen=True, slots=True)
class HandoverSpec:
    SCHEMA_VERSION: ClassVar[str] = "1.0.0"
    mode: Literal["carrier_object", "event_roles"] = "carrier_object"
    carrier_object_type: str | None = "message"
    send_qualifiers: tuple[str, ...] = ("sent",)
    receive_qualifiers: tuple[str, ...] = ("received",)
    actor_object_type: str = "employee"
    sender_qualifiers: tuple[str, ...] = ("sender", "actor")
    receiver_qualifiers: tuple[str, ...] = ("receiver", "actor")
    multi_receiver: Literal["each", "reject"] = "each"
    include_self: bool = False
    group_by_object_attribute: str | None = None
    time_precision: TimePrecision | None = None
    max_links: int = 100_000

    def __post_init__(self):
        if self.mode not in ("carrier_object", "event_roles"):
            raise ValueError("unsupported handover mode")
        if self.mode == "carrier_object" or self.carrier_object_type is not None:
            _text(self.carrier_object_type, "carrier_object_type")
        _text(self.actor_object_type, "actor_object_type")
        if self.group_by_object_attribute is not None:
            _text(self.group_by_object_attribute, "group_by_object_attribute")
        for name in (
            "send_qualifiers",
            "receive_qualifiers",
            "sender_qualifiers",
            "receiver_qualifiers",
        ):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not values:
                raise ValueError(f"{name} must be a nonempty tuple")
            for value in values:
                _text(value, name, blank=True)
            object.__setattr__(self, name, tuple(sorted(set(values))))
        if set(self.send_qualifiers) & set(self.receive_qualifiers):
            raise ValueError("send and receive carrier qualifiers must be disjoint")
        if self.multi_receiver not in ("each", "reject"):
            raise ValueError("multi_receiver must be 'each' or 'reject'")
        if type(self.include_self) is not bool:
            raise TypeError("include_self must be bool")
        if type(self.max_links) is not int or self.max_links < 1:
            raise ValueError("max_links must be a positive integer")
        validate_precision(self.time_precision)


@dataclass(frozen=True, slots=True)
class HandoverLink:
    carrier_object_id: str | None
    send_event_id: str
    receive_event_id: str | None
    sender: str
    receiver: str
    send_relations: tuple[E2OEvidence, ...]
    receive_relations: tuple[E2OEvidence, ...]
    latency_lower_microseconds: int | None
    latency_upper_microseconds: int | None


@dataclass(frozen=True, slots=True)
class HandoverEdge:
    sender: str
    receiver: str
    link_count: int
    carrier_count: int
    timed_count: int
    latency_lower_min_microseconds: int | None
    latency_upper_max_microseconds: int | None


@dataclass(frozen=True, slots=True)
class HandoverNetwork:
    actors: tuple[str, ...]
    edges: tuple[HandoverEdge, ...]
    links: tuple[HandoverLink, ...]
    group_edges: tuple[HandoverEdge, ...]
    send_count: int
    receive_count: int
    unmatched_sends: tuple[str, ...]
    unmatched_receives: tuple[str, ...]
    order_conflicts: tuple[tuple[str, str], ...]
