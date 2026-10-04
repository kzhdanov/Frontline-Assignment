from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ToolEvent


def load_reference_trace(name: str) -> tuple[list[dict[str, Any]], list[ToolEvent], str, str]:
    path = Path(__file__).parent / "fixtures" / f"{name}_trace.json"
    if not path.is_file():
        raise ValueError(f"No offline reference trace for scenario {name!r}")
    data = json.loads(path.read_text(encoding="utf-8"))
    events = [ToolEvent(**item) for item in data["tool_events"]]
    return data["messages"], events, data["termination_reason"], data["source"]

