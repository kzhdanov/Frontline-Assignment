from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ToolEvent
from .trace import derive_tool_events


def load_trace_file(path: Path) -> tuple[list[dict[str, Any]], list[ToolEvent], str, str]:
    if not path.is_file():
        raise ValueError(f"Trace file does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        messages = data["messages"]
        termination = data["termination_reason"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"Invalid trace file {path}: {exc}") from exc
    if not isinstance(messages, list) or not isinstance(termination, str):
        raise ValueError(f"Invalid trace file {path}: messages must be a list and termination_reason a string")
    events = derive_tool_events(messages)
    # A trace cannot self-assert that it is trusted fixture or live evidence.
    return messages, events, termination, "external_agent_trace"


def load_reference_trace(name: str) -> tuple[list[dict[str, Any]], list[ToolEvent], str, str]:
    messages, events, termination, _source = load_trace_file(
        Path(__file__).parent / "fixtures" / f"{name}_trace.json"
    )
    return messages, events, termination, "synthetic_reference_trace"
