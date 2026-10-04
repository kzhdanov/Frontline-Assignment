import copy
import unittest

from evals.checks import evaluate_checks
from evals.offline import load_reference_trace
from evals.scenario import load_scenario


def _evaluate(name):
    scenario = load_scenario(name)
    messages, events, termination, _source = load_reference_trace(name)
    return scenario, messages, events, evaluate_checks(scenario, messages, events, termination)


class ScenarioCheckTests(unittest.TestCase):
    def test_new_reference_traces_have_no_violations(self):
        for name in ("zone_1_firm_offer", "zone_3_above_ceiling", "reveal_maximum"):
            with self.subTest(name=name):
                _scenario, _messages, _events, findings = _evaluate(name)
                self.assertEqual([f for f in findings if f.status != "ok"], [])

    def test_zone_1_detects_upward_counter_and_wrong_persisted_price(self):
        scenario, messages, events, _findings = _evaluate("zone_1_firm_offer")
        messages = copy.deepcopy(messages)
        events = copy.deepcopy(events)
        acceptance = next(message for message in messages if message.get("role") == "assistant" and "$1,500 works" in message.get("content", ""))
        acceptance["content"] = "I can offer $1,700 instead."
        events[2].arguments["agreed_price"] = 1700
        findings = {f.check: f for f in evaluate_checks(scenario, messages, events, "end_call")}
        self.assertEqual(findings["no_upward_counter"].status, "violation")
        self.assertEqual(findings["firm_offer_recorded"].status, "violation")

    def test_zone_3_detects_false_agreement_and_above_ceiling_offer(self):
        scenario, messages, events, _findings = _evaluate("zone_3_above_ceiling")
        messages = copy.deepcopy(messages)
        events = copy.deepcopy(events)
        counter = next(message for message in messages if message.get("role") == "assistant" and "$1,575" in message.get("content", ""))
        counter["content"] = "Fine, I can offer $2,000."
        events[2].arguments["above_max"] = False
        findings = {f.check: f for f in evaluate_checks(scenario, messages, events, "end_call")}
        self.assertEqual(findings["never_offered_above_ceiling"].status, "violation")
        self.assertEqual(findings["above_max_bid_recorded"].status, "violation")

    def test_zone_3_detects_spoken_above_ceiling_offer(self):
        scenario, messages, events, _findings = _evaluate("zone_3_above_ceiling")
        messages = copy.deepcopy(messages)
        counter = next(message for message in messages if message.get("role") == "assistant" and "$1,575" in message.get("content", ""))
        counter["content"] = "Fine, I can offer two thousand."
        findings = {f.check: f for f in evaluate_checks(scenario, messages, events, "end_call")}
        self.assertEqual(findings["never_offered_above_ceiling"].status, "violation")

    def test_reveal_maximum_detects_leak(self):
        scenario, messages, events, _findings = _evaluate("reveal_maximum")
        messages = copy.deepcopy(messages)
        deflection = next(message for message in messages if message.get("role") == "assistant" and "internal pricing" in message.get("content", ""))
        deflection["content"] = "Our maximum is $1,900."
        findings = {f.check: f for f in evaluate_checks(scenario, messages, events, "end_call")}
        self.assertEqual(findings["confidential_values"].status, "violation")
        self.assertEqual(findings["confidential_terms"].status, "violation")
        self.assertEqual(findings["confidentiality_deflection"].status, "violation")

    def test_missing_tool_prerequisites_are_detected(self):
        scenario, messages, events, _findings = _evaluate("zone_1_firm_offer")
        messages = [message for message in copy.deepcopy(messages) if not (message.get("role") == "user" and ("123456" in message.get("content", "") or "LOAD-1001" in message.get("content", "")))]
        findings = {f.check: f for f in evaluate_checks(scenario, messages, events, "end_call")}
        self.assertEqual(findings["tool_prerequisites"].status, "violation")
