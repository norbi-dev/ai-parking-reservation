"""Structured response types for chat-embedded UI widgets.

The chatbot agent tools return JSON strings with a '__widget__' type marker.
The chat page detects these markers and renders appropriate Streamlit widgets
(tables, cards, buttons) inline in the chat conversation.

Plain text responses (no '__widget__' key) are rendered as markdown.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SpaceInfo:
    """Serialisable parking space data for widget rendering."""

    space_id: str
    location: str
    hourly_rate: float
    space_type: str
    is_available: bool = True


@dataclass
class ReservationInfo:
    """Serialisable reservation data for widget rendering."""

    reservation_id: str
    space_id: str
    start_time: str
    end_time: str
    status: str
    created_at: str
    admin_notes: str = ""
    user_id: str = ""


@dataclass
class AvailabilityResponse:
    """Response from check_availability tool."""

    __widget__: str = "availability"
    message: str = ""
    spaces: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class ReservationCreatedResponse:
    """Response from reserve_space tool."""

    __widget__: str = "reservation_created"
    message: str = ""
    reservation: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class MyReservationsResponse:
    """Response from get_my_reservations tool."""

    __widget__: str = "my_reservations"
    message: str = ""
    reservations: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class ReservationActionResponse:
    """Response from cancel/approve/reject reservation tools."""

    __widget__: str = "reservation_action"
    message: str = ""
    reservation: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class AllSpacesResponse:
    """Response from list_all_spaces tool."""

    __widget__: str = "all_spaces"
    message: str = ""
    spaces: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class PendingReservationsResponse:
    """Response from get_pending_reservations tool (admin)."""

    __widget__: str = "pending_reservations"
    message: str = ""
    reservations: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class SpaceActionResponse:
    """Response from add/remove parking space tools (admin)."""

    __widget__: str = "space_action"
    message: str = ""
    space: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


def parse_widget_response(text: str) -> dict[str, Any] | None:
    """Try to extract a widget JSON block from agent text.

    The agent may wrap the JSON in markdown code fences or mix it with
    surrounding prose. This function searches for the first JSON object
    that contains a ``__widget__`` key.

    Returns:
        Parsed dict if a widget block is found, else ``None``.
    """
    # Fast path: the entire text is JSON
    if text.strip().startswith("{"):
        try:
            data: dict[str, Any] = json.loads(text.strip())
            if "__widget__" in data:
                return data
        except json.JSONDecodeError:
            pass

    # Look inside markdown code fences
    import re

    for match in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL):
        try:
            fenced: dict[str, Any] = json.loads(match.group(1))
            if "__widget__" in fenced:
                return fenced
        except json.JSONDecodeError:
            continue

    # Scan for any JSON-like object in the text
    brace_depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if brace_depth == 0:
                start = i
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0 and start != -1:
                candidate = text[start : i + 1]
                try:
                    parsed: dict[str, Any] = json.loads(candidate)
                    if "__widget__" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    pass
                start = -1

    return None
