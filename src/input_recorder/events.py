"""Recorded input events and how they are stored.

Version 1 wrote the recording straight into Python code. Keeping the events as
data (JSON) first means a recording can be replayed, edited, trimmed or turned
into a script later, and the code generator can be tested on its own.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

Kind = Literal["key_down", "key_up", "mouse_down", "mouse_up", "move"]
KINDS = {"key_down", "key_up", "mouse_down", "mouse_up", "move"}

# Special keys are stored by name ("special:enter"). Only plain identifiers are
# allowed, so a recording file can never inject code into a generated script.
_SPECIAL = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class Event:
    t: float                      # seconds since the recording started
    kind: Kind
    key: str | None = None        # "char:a" or "special:enter"
    x: int | None = None
    y: int | None = None
    button: str | None = None     # "left", "right", "middle"

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown event kind: {self.kind}")
        if self.t < 0:
            raise ValueError("event time can't be negative")
        if self.kind.startswith("key"):
            validate_key(self.key)
        if self.kind.startswith("mouse") and self.button not in {"left", "right", "middle"}:
            raise ValueError(f"unknown mouse button: {self.button}")


def validate_key(key: str | None) -> None:
    if not key or ":" not in key:
        raise ValueError(f"invalid key: {key!r}")
    prefix, value = key.split(":", 1)
    if prefix == "char":
        if len(value) != 1:
            raise ValueError(f"char key must be one character: {key!r}")
    elif prefix == "special":
        if not _SPECIAL.match(value):
            raise ValueError(f"invalid special key name: {key!r}")
    else:
        raise ValueError(f"invalid key prefix: {key!r}")


def thin_moves(events: list[Event], min_interval: float = 0.02) -> list[Event]:
    """Drops mouse moves closer than ``min_interval`` seconds to the previous kept move.

    Mouse listeners fire hundreds of move events per second; most add size
    without changing what gets replayed. Clicks and keys are always kept, and a
    move right before a click is kept so the click lands in the right place.
    """
    result: list[Event] = []
    last_move_t: float | None = None
    for i, ev in enumerate(events):
        if ev.kind != "move":
            result.append(ev)
            continue
        next_is_click = i + 1 < len(events) and events[i + 1].kind.startswith("mouse")
        if last_move_t is None or ev.t - last_move_t >= min_interval or next_is_click:
            result.append(ev)
            last_move_t = ev.t
    return result


def save(events: list[Event], path: str | Path) -> None:
    data = {"version": 1, "events": [asdict(e) for e in events]}
    Path(path).write_text(json.dumps(data, indent=1), encoding="utf-8")


def load(path: str | Path) -> list[Event]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise ValueError("unsupported recording version")
    return [Event(**e) for e in data["events"]]
