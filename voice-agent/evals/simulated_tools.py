from __future__ import annotations

from copy import deepcopy
from typing import Any

from tool_contracts import openai_tool_schema

from .models import ToolEvent
from .scenario import Scenario


EVAL_TOOL_NAMES = ("verify_carrier", "get_load_context", "record_agreement", "end_call", "transfer_to_human")
TOOL_SCHEMAS = [openai_tool_schema(name) for name in EVAL_TOOL_NAMES]


def production_tool_schemas() -> list[dict[str, Any]]:
    return deepcopy(TOOL_SCHEMAS)


class SimulatedTools:
    """No-I/O implementations of the production-facing tool contracts."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.events: list[ToolEvent] = []
        self.carrier_verified = False
        self.load_loaded = False
        self.ended = False

    def execute(self, name: str, arguments: dict[str, Any], turn: int) -> dict[str, Any]:
        handler = getattr(self, f"_{name}", None)
        result = handler(arguments) if handler else {"status": "error", "message": f"Unsupported tool: {name}"}
        self.events.append(ToolEvent(len(self.events) + 1, turn, name, deepcopy(arguments), deepcopy(result)))
        return result

    def _verify_carrier(self, args: dict[str, Any]) -> dict[str, Any]:
        if str(args.get("mc_number", "")).replace("MC", "").strip(" -") != self.scenario.carrier["mc_number"]:
            return {"status": "not_found", "message": "No carrier found"}
        self.carrier_verified = True
        return {"status": "success", "message": f"Carrier found: {self.scenario.carrier['name']}", "carrier_name": self.scenario.carrier["name"], "mc_number": self.scenario.carrier["mc_number"]}

    def _get_load_context(self, args: dict[str, Any]) -> dict[str, Any]:
        if str(args.get("load_id", "")).upper() != self.scenario.load["id"].upper():
            return {"status": "error", "message": "No load found with that reference"}
        self.load_loaded = True
        return {"status": "success", "message": "Load information retrieved", "load_data": deepcopy(self.scenario.load)}

    def _record_agreement(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self.load_loaded:
            return {"status": "error", "message": "Load not loaded"}
        return {"status": "success", "message": "Agreement recorded", "negotiation_id": "eval-negotiation-1"}

    def _end_call(self, args: dict[str, Any]) -> dict[str, Any]:
        self.ended = True
        return {"status": "success", "message": "Call ending", "reason": args.get("reason")}

    def _transfer_to_human(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"status": "error", "message": "Transfer is not expected in this scenario"}
