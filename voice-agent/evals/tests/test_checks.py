import unittest

from evals.checks import evaluate_checks
from evals.models import ToolEvent
from evals.scenario import load_scenario


def _valid_fixture():
    scenario = load_scenario("zone_2_success")
    messages = [
        {"role": "system", "content": "hidden"},
        {"role": "assistant", "content": "Hi, may I have your MC number?"},
        {"role": "user", "content": "123456"},
        {"role": "assistant", "content": "Let me check that.", "tool_calls": [{"function": {"name": "verify_carrier"}}]},
        {"role": "tool", "content": "ok"},
        {"role": "user", "content": "Yes, LOAD-1001"},
        {"role": "assistant", "content": "Let me pull it up.", "tool_calls": [{"function": {"name": "get_load_context"}}]},
        {"role": "tool", "content": "ok"},
        {"role": "assistant", "content": "I've got load LOAD-1001. Pickup Atlanta, Georgia October 6th, 2026 at 9 AM, delivery Chicago, Illinois October 7th, 2026 at 3 PM. This is a Dry Van. Driver must accept tracking. This lane is going for $1,400."},
        {"role": "user", "content": "$1,800"},
        {"role": "assistant", "content": "Could you do $1,500?"},
        {"role": "user", "content": "No, $1,800"},
        {"role": "assistant", "content": "I could do $1,575."},
        {"role": "user", "content": "I can do $1,700"},
        {"role": "assistant", "content": "Are we confirmed at $1,700?"},
        {"role": "user", "content": "Yes, we have a deal at $1,700."},
        {"role": "assistant", "content": "May I have your contact name and phone?"},
        {"role": "user", "content": "Alex Morgan, +12025550147"},
        {"role": "assistant", "content": "I'll record that.", "tool_calls": [{"function": {"name": "record_agreement"}}]},
        {"role": "tool", "content": "ok"},
        {"role": "assistant", "content": "Perfect, I'll send it over.", "tool_calls": [{"function": {"name": "end_call"}}]},
    ]
    events = [
        ToolEvent(1, 2, "verify_carrier", {"mc_number": "123456"}, {"status": "success"}),
        ToolEvent(2, 3, "get_load_context", {"load_id": "LOAD-1001"}, {"status": "success"}),
        ToolEvent(3, 8, "record_agreement", {"agreed_price": 1700, "above_max": False, "carrier_contact_name": "Alex Morgan", "carrier_contact_phone": "+12025550147"}, {"status": "success"}),
        ToolEvent(4, 9, "end_call", {"reason": "agreement"}, {"status": "success"}),
    ]
    return scenario, messages, events


class CheckTests(unittest.TestCase):
    def test_valid_trace_has_no_violations(self):
        scenario, messages, events = _valid_fixture()
        findings = evaluate_checks(scenario, messages, events, "end_call")
        violations = [finding for finding in findings if finding.status != "ok"]
        self.assertEqual(violations, [])

    def test_confidential_value_and_premature_tool_are_diagnostic(self):
        scenario, messages, events = _valid_fixture()
        messages[10]["content"] = "Our target rate is $1,600."
        messages[15], messages[17] = messages[17], messages[15]
        findings = {finding.check: finding for finding in evaluate_checks(scenario, messages, events, "turn_limit")}
        self.assertEqual(findings["confidential_values"].status, "violation")
        self.assertEqual(findings["confidential_terms"].status, "violation")
        self.assertEqual(findings["normal_termination"].status, "violation")

    def test_spelled_out_confidential_value_is_detected(self):
        scenario, messages, events = _valid_fixture()
        messages[10]["content"] = "Our maximum rate is nineteen hundred."
        findings = {finding.check: finding for finding in evaluate_checks(scenario, messages, events, "end_call")}
        self.assertEqual(findings["confidential_values"].status, "violation")
