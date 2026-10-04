import json
import unittest

from evals.conversation import run_conversation
from evals.openai_client import ModelResponse
from evals.scenario import load_scenario


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

