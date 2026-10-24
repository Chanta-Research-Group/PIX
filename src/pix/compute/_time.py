"""Exact arithmetic for declared observation intervals (never invented offsets)."""

from datetime import datetime, timedelta

from pix.contracts.time import TimePrecision


def micros(delta: timedelta) -> int:
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def width(event, precision: TimePrecision | None) -> int:
    if precision is None:
        return 0
    value = precision.granularity_microseconds
    if precision.attribute is not None:
        value = {a.name: a.value for a in event.attributes}.get(precision.attribute)
    if type(value) is not int or value < 1:
        raise ValueError("selected precision attribute must be a positive integer")
    return 0 if value == 1 else value


def interval(
    event, precision: TimePrecision | None
) -> tuple[datetime, datetime | None]:
    span = width(event, precision)
    attrs = {a.name: a.value for a in event.attributes}
    if attrs.get("time_basis") == "anchor_previous_observed":
        lower, upper = attrs.get("time_lower"), attrs.get("time_upper")
        if not isinstance(lower, datetime) or (
            upper is not None and not isinstance(upper, datetime)
        ):
            raise ValueError("anchor bounds must be datetime attributes")
        if lower != event.time or (upper is not None and upper < lower):
            raise ValueError("anchor bounds must contain the anchor timestamp")
        return lower, upper
    return event.time, event.time + timedelta(microseconds=span)


def elapsed(source, target):
    """Conservative closed bounds enclosing the half-open observation interval."""
    sl, su = source
    tl, tu = target
    return (
        None if su is None else micros(tl - su),
        None if tu is None else micros(tu - sl),
    )
