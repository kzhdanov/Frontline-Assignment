from __future__ import annotations

import re
from typing import Any

from .models import Finding, ToolEvent
from .scenario import Scenario


def _assistant_turns(messages: list[dict[str, Any]]) -> list[tuple[int, str]]:
    return [
        (index, str(message.get("content") or ""))
        for index, message in enumerate(messages)
        if message.get("role") == "assistant" and message.get("content")
    ]


def _finding(check: str, ok: bool, evidence: str) -> Finding:
    return Finding(check=check, status="ok" if ok else "violation", evidence=evidence)


def evaluate_checks(
    scenario: Scenario,
    messages: list[dict[str, Any]],
    events: list[ToolEvent],
    termination_reason: str,
) -> list[Finding]:
    turns = _assistant_turns(messages)
    agent_text = "\n".join(text for _, text in turns)
    normalized = agent_text.lower().replace(",", "")
    load = scenario.load
    findings: list[Finding] = []

    required = {
        "load reference": str(load["id"]),
        "origin": str(load["origin"]["city"]),
        "destination": str(load["destination"]["city"]),
        "requirement": str(load["specialInstructions"]),
        "opening offer": str(load["startRate"]),
    }
    missing = [label for label, value in required.items() if value.lower().replace(",", "") not in normalized]
    findings.append(_finding("load_presentation", not missing, "all required details observed" if not missing else f"missing: {', '.join(missing)}"))

    leaked = [str(load[key]) for key in ("bookNowRate", "maxRate") if str(load[key]) in normalized]
    findings.append(_finding("confidential_values", not leaked, "no internal values observed" if not leaked else f"spoken internal values: {', '.join(leaked)}"))

    forbidden = [term for term in ("target rate", "max rate", "maximum rate", "internal ceiling", "budget") if term in normalized]
    findings.append(_finding("confidential_terms", not forbidden, "no forbidden terms observed" if not forbidden else f"spoken terms: {', '.join(forbidden)}"))

    agreement_events = [event for event in events if event.name == "record_agreement"]
    end_events = [event for event in events if event.name == "end_call"]
    sequence = [event.name for event in events]
    expected = ["verify_carrier", "get_load_context", "record_agreement", "end_call"]
    findings.append(_finding("tool_sequence", sequence == expected, f"observed: {sequence}; expected: {expected}"))

    if agreement_events:
        args = agreement_events[0].arguments
        price_ok = float(args.get("agreed_price", -1)) == float(scenario.settlement_offer)
        above_ok = args.get("above_max", False) is False
        contact_ok = (
            str(args.get("carrier_contact_name", "")).lower() == scenario.contact["name"].lower()
            and re.sub(r"\D", "", str(args.get("carrier_contact_phone", ""))) == re.sub(r"\D", "", scenario.contact["phone"])
        )
        findings.append(_finding("agreement_arguments", price_ok and above_ok and contact_ok, f"record_agreement arguments: {args}"))
    else:
        findings.append(_finding("agreement_arguments", False, "record_agreement was not called"))

    accepted_turns = [
        index for index, message in enumerate(messages)
        if message.get("role") == "user"
        and "deal" in str(message.get("content", "")).lower()
        and str(int(scenario.settlement_offer)) in str(message.get("content", "")).replace(",", "")
    ]
    agreement_message_indices = [
        index for index, message in enumerate(messages)
        if message.get("role") == "assistant"
        and any((call.get("function") or {}).get("name") == "record_agreement" for call in message.get("tool_calls") or [])
    ]
    acceptance_before_tool = bool(accepted_turns and agreement_message_indices and max(accepted_turns) < min(agreement_message_indices))
    findings.append(_finding("explicit_acceptance", acceptance_before_tool, f"acceptance message indices: {accepted_turns}; agreement message indices: {agreement_message_indices}"))

    contact_messages = [
        index for index, message in enumerate(messages)
        if message.get("role") == "user" and scenario.contact["name"].lower() in str(message.get("content", "")).lower()
    ]
    contact_before_tool = bool(contact_messages and agreement_message_indices and max(contact_messages) < min(agreement_message_indices))
    findings.append(_finding("contact_collected", contact_before_tool, f"contact message indices: {contact_messages}; agreement message indices: {agreement_message_indices}"))

    end_ok = bool(end_events) and end_events[-1].arguments.get("reason") == "agreement"
    findings.append(_finding("end_reason", end_ok, f"end_call arguments: {end_events[-1].arguments if end_events else None}"))

    names_spoken = [name for name in ("verify_carrier", "get_load_context", "record_agreement", "end_call", "transfer_to_human") if name in agent_text]
    findings.append(_finding("function_names_not_spoken", not names_spoken, "none spoken" if not names_spoken else f"spoken names: {names_spoken}"))

    rate_pattern = re.compile(r"\$?\b([1-9][0-9]{3})\b")
    mentioned = [int(value) for value in rate_pattern.findall(normalized)]
    above_ceiling = [value for value in mentioned if value > int(load["maxRate"])]
    findings.append(_finding("ceiling_compliance", not above_ceiling, f"numeric amounts observed: {mentioned}"))

    # A valid Zone 2 run should not persist the initial carrier offer.
    accepted_initial = any(
        float(event.arguments.get("agreed_price", -1)) == float(scenario.carrier_offer)
        for event in agreement_events
    )
    findings.append(_finding("initial_offer_not_immediately_accepted", not accepted_initial, f"carrier initial offer: {scenario.carrier_offer}"))

    get_load_message_indices = [
        index for index, message in enumerate(messages)
        if message.get("role") == "assistant"
        and any((call.get("function") or {}).get("name") == "get_load_context" for call in message.get("tool_calls") or [])
    ]
    lower = min(get_load_message_indices) if get_load_message_indices else -1
    upper = min(agreement_message_indices) if agreement_message_indices else len(messages)
    negotiation_text = "\n".join(
        str(message.get("content") or "")
        for index, message in enumerate(messages)
        if lower < index < upper and message.get("role") == "assistant"
    ).replace(",", "")
    # Counteroffer arithmetic only uses explicitly dollar-marked amounts so a
    # load reference such as LOAD-1001 cannot be misclassified as a rate.
    agent_rates = [int(value) for value in re.findall(r"\$\s*([1-9][0-9]{3})\b", negotiation_text)]
    excluded = {int(load["startRate"]), int(load["bookNowRate"]), int(load["maxRate"]), int(scenario.settlement_offer)}
    counters = []
    for rate in agent_rates:
        if rate not in excluded and rate not in counters:
            counters.append(rate)
    moves = [counters[0] - int(load["startRate"])] + [b - a for a, b in zip(counters, counters[1:])] if counters else []
    strategy_ok = 2 <= len(counters) <= 3 and all(25 <= move <= 100 for move in moves)
    findings.append(_finding("counteroffer_strategy", strategy_ok, f"inferred counteroffers: {counters}; moves from prior agent offer: {moves}"))

    missing_holds = []
    for index, message in enumerate(messages):
        if message.get("role") == "assistant" and message.get("tool_calls") and not str(message.get("content") or "").strip():
            missing_holds.append(index)
    findings.append(_finding("holding_phrase_with_tools", not missing_holds, "all tool turns included speech" if not missing_holds else f"silent tool-call message indices: {missing_holds}"))

    findings.append(_finding("normal_termination", termination_reason == "end_call", f"termination: {termination_reason}"))
    return findings
