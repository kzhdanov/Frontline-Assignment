from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Scenario:
    name: str
    version: int
    organization: str
    carrier: dict[str, str]
    contact: dict[str, str]
    load: dict[str, Any]
    carrier_offer: float
    settlement_offer: float
    max_turns: int
    expectations: dict[str, Any]

    @classmethod
    def load_file(cls, path: Path) -> "Scenario":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)


def load_scenario(name: str) -> Scenario:
    path = Path(__file__).parent / "scenarios" / f"{name}.json"
    if not path.is_file():
        available = ", ".join(p.stem for p in path.parent.glob("*.json"))
        raise ValueError(f"Unknown scenario {name!r}. Available: {available}")
    return Scenario.load_file(path)
