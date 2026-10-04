import unittest

from evals.scenario import load_scenario
from evals.simulated_tools import SimulatedTools


class SimulatedToolsTests(unittest.TestCase):
    def test_happy_path_tools_are_in_memory_and_traced(self):
        scenario = load_scenario("zone_2_success")
        tools = SimulatedTools(scenario)

        self.assertEqual(tools.execute("verify_carrier", {"mc_number": "123456"}, 1)["status"], "success")
        self.assertEqual(tools.execute("get_load_context", {"load_id": "LOAD-1001"}, 2)["status"], "success")
        self.assertEqual(tools.execute("record_agreement", {"agreed_price": 1700}, 3)["status"], "success")
        self.assertEqual(tools.execute("end_call", {"reason": "agreement"}, 4)["status"], "success")

        self.assertEqual([event.name for event in tools.events], [
            "verify_carrier", "get_load_context", "record_agreement", "end_call"
        ])
        self.assertTrue(tools.ended)

    def test_wrong_fixture_values_fail_closed(self):
        scenario = load_scenario("zone_2_success")
        tools = SimulatedTools(scenario)

        self.assertEqual(tools.execute("verify_carrier", {"mc_number": "999"}, 1)["status"], "not_found")
        self.assertEqual(tools.execute("get_load_context", {"load_id": "OTHER"}, 2)["status"], "error")
        self.assertEqual(tools.execute("record_agreement", {"agreed_price": 1700}, 3)["status"], "error")
