from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import ToolEvent
from .scenario import Scenario


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "verify_carrier",
            "description": "Verify the carrier's identity using their MC number.",
            "parameters": {
                "type": "object",
                "properties": {"mc_number": {"type": "string"}},
                "required": ["mc_number"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_load_context",
            "description": "Retrieve detailed information about a freight load.",
            "parameters": {
                "type": "object",
                "properties": {"load_id": {"type": "string"}},
                "required": ["load_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_agreement",
            "description": "Record a negotiation agreement or above-max bid.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agreed_price": {"type": "number"},
                    "above_max": {"type": "boolean"},
                    "carrier_contact_name": {"type": "string"},
                    "carrier_contact_phone": {"type": "string"},
                },
                "required": ["agreed_price"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "end_call",
            "description": "End the call with a specific reason.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "enum": ["abrupt", "agreement", "no_agreement", "bid_placed", "error", "load_not_found", "mc_not_found"],
                    }
                },
                "required": ["reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "Transfer the call to a human broker only after load lookup.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "load_number": {"type": "string"},
                    "price_asked_by_carrier": {"type": "number"},
                    "best_price_offered_by_bot": {"type": "number"},
                },
                "required": ["reason", "load_number"],
                "additionalProperties": False,
            },
        },
    },
]


def production_tool_schemas() -> list[dict[str, Any]]:
    """Use the canonical schemas when Pipecat is installed; fallback keeps unit tests lightweight."""
    try:
        from tool_definitions import (
            END_CALL_FUNCTION,
            GET_LOAD_CONTEXT_FUNCTION,
            RECORD_AGREEMENT_FUNCTION,
            TRANSFER_TO_HUMAN_FUNCTION,
            VERIFY_CARRIER_FUNCTION,
        )
    except ImportError:
        return deepcopy(TOOL_SCHEMAS)
    definitions = (
        VERIFY_CARRIER_FUNCTION,
        GET_LOAD_CONTEXT_FUNCTION,
        RECORD_AGREEMENT_FUNCTION,
        END_CALL_FUNCTION,
        TRANSFER_TO_HUMAN_FUNCTION,
    )
    schemas = []
    for definition in definitions:
        raw = definition.to_default_dict()
        schemas.append(raw if raw.get("type") == "function" else {"type": "function", "function": raw})
    return schemas


class SimulatedTools:
    """No-I/O implementations of the production-facing tool contracts."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.events: list[ToolEvent] = []
        self.load_loaded = False
        self.ended = False

    def execute(self, name: str, arguments: dict[str, Any], turn: int) -> dict[str, Any]:
        handler = getattr(self, f"_{name}", None)
        if handler is None:
            result = {"status": "error", "message": f"Unsupported tool: {name}"}
        else:
            result = handler(arguments)
        self.events.append(ToolEvent(len(self.events) + 1, turn, name, deepcopy(arguments), deepcopy(result)))
        return result

    def _verify_carrier(self, args: dict[str, Any]) -> dict[str, Any]:
        if str(args.get("mc_number", "")).replace("MC", "").strip(" -") != self.scenario.carrier["mc_number"]:
            return {"status": "not_found", "message": "No carrier found"}
        return {
            "status": "success",
            "message": f"Carrier found: {self.scenario.carrier['name']}",
            "carrier_name": self.scenario.carrier["name"],
            "mc_number": self.scenario.carrier["mc_number"],
        }

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
