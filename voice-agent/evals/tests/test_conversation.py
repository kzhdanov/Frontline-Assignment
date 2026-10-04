import json
import unittest

from evals.conversation import run_conversation
from evals.caller import Zone2Caller
from evals.checks import evaluate_checks
from evals.openai_client import ModelResponse
from evals.scenario import load_scenario
from evals.trace import derive_tool_events


def _text(content):
    return ModelResponse({"role": "assistant", "content": content}, {})


def _tool(call_id, name, arguments, content="Let me check that."):
    return ModelResponse({
        "role": "assistant",
        "content": content,
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)},
        }],
    }, {})


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.system_prompts = []

    def complete(self, **kwargs):
        self.system_prompts.append(kwargs["messages"][0]["content"])
        return next(self.responses)


class ConversationTests(unittest.TestCase):
    def test_complete_conversation_uses_prompt_transition_and_safe_tools(self):
        scenario = load_scenario("zone_2_success")
        client = FakeClient([
            _text("Thanks for calling KCH. May I have your MC number?"),
            _tool("1", "verify_carrier", {"mc_number": "123456"}),
            _text("I found Northstar Transport LLC. Is that you? What reference are you calling about?"),
            _tool("2", "get_load_context", {"load_id": "LOAD-1001"}, "Let me pull it up."),
            _text("I've got load LOAD-1001 from Atlanta to Chicago. Driver must accept tracking. This lane is going for $1,400."),
            _text("Could you do $1,500?"),
            _text("I can move to $1,575."),
            _text("Are we confirmed at $1,700?"),
            _text("Great. May I have your contact name and phone?"),
            _tool("3", "record_agreement", {
                "agreed_price": 1700,
                "above_max": False,
                "carrier_contact_name": "Alex Morgan",
                "carrier_contact_phone": "+12025550147",
            }, "I'll record that."),
            _tool("4", "end_call", {"reason": "agreement"}, "Perfect, I'll send it over."),
        ])

        messages, tools, termination, _usage = run_conversation(scenario, client, "test-agent")

        self.assertEqual(termination, "end_call")
        self.assertEqual([event.name for event in tools.events], [
            "verify_carrier", "get_load_context", "record_agreement", "end_call"
        ])
        self.assertNotIn("CONFIDENTIAL PRICING", client.system_prompts[0])
        self.assertIn("CONFIDENTIAL PRICING", client.system_prompts[-1])
        self.assertTrue(any(message.get("role") == "user" and "Alex Morgan" in message.get("content", "") for message in messages))

    def test_malformed_live_tool_arguments_remain_scoreable(self):
        scenario = load_scenario("zone_2_success")
        malformed = ModelResponse({
            "role": "assistant", "content": "Let me check that.",
            "tool_calls": [{"type": "function", "function": {
                "name": "verify_carrier", "arguments": "{not-json",
            }}],
        }, {})
        client = FakeClient([malformed, _tool("end", "end_call", {"reason": "error"})])
        messages, tools, termination, _usage = run_conversation(scenario, client, "test-agent")
        self.assertEqual(termination, "end_call")
        self.assertIn("_malformed_arguments", tools.events[0].arguments)
        self.assertTrue(messages[1]["tool_calls"][0]["id"].startswith("eval-"))
        findings = {item.check: item for item in evaluate_checks(
            scenario, messages, derive_tool_events(messages), termination
        )}
        self.assertEqual(findings["tool_call_validity"].status, "violation")

    def test_caller_does_not_advance_on_unrecognized_response(self):
        scenario = load_scenario("zone_2_success")
        caller = Zone2Caller(scenario)
        first = caller.next_message(assistant_text="Here are the load details.", carrier_verified=True, load_loaded=True)
        retry = caller.next_message(assistant_text="Can you clarify?", carrier_verified=True, load_loaded=True)
        counter = caller.next_message(assistant_text="I can offer $1,500.", carrier_verified=True, load_loaded=True)
        self.assertIn("$1,800", first)
        self.assertEqual(retry, "Could you repeat that for me?")
        self.assertIn("still need $1,800", counter)
