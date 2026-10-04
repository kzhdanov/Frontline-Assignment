from __future__ import annotations

import json
from typing import Any

from .models import ToolEvent


class TraceError(ValueError):
    pass


def derive_tool_events(messages: list[dict[str, Any]]) -> list[ToolEvent]:
    """Build the canonical tool trace from chat messages and reject ambiguity."""
    results: dict[str, tuple[int, dict[str, Any]]] = {}
    for message_index, message in enumerate(messages):
        if message.get("role") != "tool":
            continue
        call_id = str(message.get("tool_call_id") or "")
        if not call_id or call_id in results:
            raise TraceError(f"Missing or duplicate tool result id at message {message_index}")
        try:
            result = json.loads(str(message.get("content") or "{}"))
        except json.JSONDecodeError as exc:
            raise TraceError(f"Malformed tool result JSON at message {message_index}") from exc
        if not isinstance(result, dict):
            raise TraceError(f"Tool result must be an object at message {message_index}")
        results[call_id] = (message_index, result)

    events: list[ToolEvent] = []
    seen_calls: set[str] = set()
    for message_index, message in enumerate(messages):
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            call_id = str(call.get("id") or "")
            function = call.get("function") or {}
            name = str(function.get("name") or "")
            if not call_id or call_id in seen_calls:
                raise TraceError(f"Missing or duplicate tool call id at message {message_index}")
            if call_id not in results:
                raise TraceError(f"Missing result for tool call {call_id!r}")
            result_index, result = results[call_id]
            if result_index <= message_index:
                raise TraceError(f"Tool result precedes call {call_id!r}")
            result_message = messages[result_index]
            if result_message.get("name") and result_message.get("name") != name:
                raise TraceError(f"Tool name mismatch for call {call_id!r}")
            try:
                arguments = json.loads(str(function.get("arguments") or "{}"))
            except json.JSONDecodeError as exc:
                raise TraceError(f"Malformed arguments for tool call {call_id!r}") from exc
            if not isinstance(arguments, dict):
                raise TraceError(f"Tool arguments must be an object for call {call_id!r}")
            seen_calls.add(call_id)
            events.append(ToolEvent(len(events) + 1, message_index, name, arguments, result))

    orphans = set(results) - seen_calls
    if orphans:
        raise TraceError(f"Orphan tool results: {sorted(orphans)}")
    return events
