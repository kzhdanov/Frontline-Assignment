"""Dependency-free canonical contracts for voice-agent tools."""

from __future__ import annotations

from typing import Any


TOOL_CONTRACTS: dict[str, dict[str, Any]] = {
    "verify_carrier": {"description": "Verify the carrier's identity using their MC (Motor Carrier) number. Call this when the caller provides their MC number at the beginning of the call.", "properties": {"mc_number": {"type": "string", "description": "The MC number provided by the caller (e.g., '1233445')"}}, "required": ["mc_number"]},
    "get_load_context": {"description": "Retrieve detailed information about a freight load from the database. Call this when the caller mentions a load ID or number they want to discuss.", "properties": {"load_id": {"type": "string", "description": "The load ID or reference number (e.g., 'LOAD-1234' or just '1234')"}}, "required": ["load_id"]},
    "record_agreement": {"description": "Record a negotiation agreement or above-max bid. For regular agreements, just pass agreed_price. For above-max bids (when carrier won't go below max rate), also pass above_max=true with their contact info.", "properties": {"agreed_price": {"type": "number", "description": "The agreed price (or proposed price for above-max bids) in dollars"}, "above_max": {"type": "boolean", "description": "Set to true when storing an above-max bid for follow-up (default: false)"}, "carrier_contact_name": {"type": "string", "description": "Carrier contact name (required if above_max is true)"}, "carrier_contact_phone": {"type": "string", "description": "Carrier contact phone. Leave empty if caller says 'use this one' or similar - their caller ID will be used."}}, "required": ["agreed_price"]},
    "end_call": {"description": "End the call with a specific reason. Use 'agreement' after recording a deal, 'bid_placed' after storing an above-max bid, 'no_agreement' when carrier declines (bad fit, wrong location, etc.), 'load_not_found'/'mc_not_found' for lookup failures, 'abrupt' for disconnects, 'error' for technical issues.", "properties": {"reason": {"type": "string", "enum": ["abrupt", "agreement", "no_agreement", "bid_placed", "error", "load_not_found", "mc_not_found"], "description": "The reason for ending the call"}}, "required": ["reason"]},
    "transfer_to_human": {"description": "Transfer the call to a human broker. ONLY call this after get_load_context has succeeded.", "properties": {"reason": {"type": "string", "description": "Reason for transfer"}, "load_number": {"type": "string", "description": "Load identifier"}, "price_asked_by_carrier": {"type": "number", "description": "Carrier requested price"}, "best_price_offered_by_bot": {"type": "number", "description": "Bot offered best price"}}, "required": ["reason", "load_number"]},
    "transfer_human_to_carrier": {"description": "Transfer the human broker to the carrier's room after finishing discussion. Call this when the human broker is ready to speak directly with the carrier.", "properties": {"summary": {"type": "string", "description": "Brief summary of what was discussed with the human broker"}}, "required": ["summary"]},
}


def openai_tool_schema(name: str) -> dict[str, Any]:
    contract = TOOL_CONTRACTS[name]
    return {"type": "function", "function": {"name": name, "description": contract["description"], "parameters": {"type": "object", "properties": contract["properties"], "required": contract["required"], "additionalProperties": False}}}
