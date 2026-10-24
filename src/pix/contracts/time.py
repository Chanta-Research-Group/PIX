"""Declared observation precision, separate from timestamp storage resolution."""

from dataclasses import dataclass
from typing import ClassVar, Literal


@dataclass(frozen=True, slots=True)
class TimePrecision:
    """A recorded t denotes [t, t + g); g=1 preserves exact µs observations.

    ``attribute`` selects an integer microsecond width on every selected event.
    Missing or invalid selected attributes are errors, never silent fallbacks.
    """

    SCHEMA_VERSION: ClassVar[str] = "1.0.0"
    granularity_microseconds: int = 1
    alignment: Literal["floor"] = "floor"
    attribute: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.granularity_microseconds) is not int
            or self.granularity_microseconds < 1
        ):
            raise ValueError("granularity_microseconds must be a positive integer")
        if self.alignment != "floor":
            raise ValueError("alignment must be 'floor'")
        if self.attribute is not None and (
            not isinstance(self.attribute, str) or not self.attribute.strip()
        ):
            raise ValueError("attribute must be nonblank text or None")


def validate_precision(value: object) -> None:
    if value is not None and not isinstance(value, TimePrecision):
        raise TypeError("time_precision must be TimePrecision or None")
