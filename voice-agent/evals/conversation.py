from __future__ import annotations

import json
from typing import Any

from .caller import Zone2Caller
from .openai_client import OpenAIChatClient
from .prompts import initial_prompt, negotiation_prompt
from .scenario import Scenario
from .simulated_tools import SimulatedTools, production_tool_schemas


def _add_usage(total: dict[str, int], current: dict[str, int]) -> None:
    for key, value in current.items():
        total[key] = total.get(key, 0) + value


def run_conversation(
    scenario: Scenario,
    client: OpenAIChatClient,
    model: str,
) -> tuple[list[dict[str, Any]], SimulatedTools, str, dict[str, int]]:
    messages: list[dict[str, Any]] = [{
        "role": "system",
        "content": initial_prompt(scenario.organization),
    }]
    tools = SimulatedTools(scenario)
    caller = Zone2Caller(scenario)
    usage: dict[str, int] = {}
    schemas = production_tool_schemas()

    for turn in range(1, scenario.max_turns + 1):
        response = client.complete(model=model, messages=messages, tools=schemas, temperature=0.7)
        _add_usage(usage, response.usage)
        assistant = dict(response.message)
        assistant.setdefault("content", "")
        messages.append(assistant)

        tool_calls = assistant.get("tool_calls") or []
        if tool_calls:
            for call in tool_calls:
                function = call.get("function") or {}
                name = function.get("name", "")
                try:
                    arguments = json.loads(function.get("arguments") or "{}")
                except json.JSONDecodeError:
                    arguments = {"_malformed_arguments": function.get("arguments")}
                result = tools.execute(name, arguments, turn)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", f"eval-{len(tools.events)}"),
                    "name": name,
                    "content": json.dumps(result),
                })
                if name == "get_load_context" and result.get("status") == "success":
                    messages[0] = {"role": "system", "content": negotiation_prompt(scenario.load)}
            if tools.ended:
                return messages, tools, "end_call", usage
            continue

        caller_text = caller.next_message(
            load_loaded=tools.load_loaded,
            tool_names=[event.name for event in tools.events],
        )
        messages.append({"role": "user", "content": caller_text})

    return messages, tools, "turn_limit", usage
