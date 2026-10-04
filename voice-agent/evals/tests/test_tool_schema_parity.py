import unittest

from evals.simulated_tools import TOOL_SCHEMAS


class ToolSchemaParityTests(unittest.TestCase):
    def test_fallback_contract_matches_canonical_when_available(self):
        try:
            from tool_definitions import (
                END_CALL_FUNCTION,
                GET_LOAD_CONTEXT_FUNCTION,
                RECORD_AGREEMENT_FUNCTION,
                TRANSFER_TO_HUMAN_FUNCTION,
                VERIFY_CARRIER_FUNCTION,
            )
        except ImportError as exc:
            self.skipTest(f"Pipecat production schemas are not installed: {exc}")

        canonical = (
            VERIFY_CARRIER_FUNCTION,
            GET_LOAD_CONTEXT_FUNCTION,
            RECORD_AGREEMENT_FUNCTION,
            END_CALL_FUNCTION,
            TRANSFER_TO_HUMAN_FUNCTION,
        )
        fallback_by_name = {item["function"]["name"]: item["function"] for item in TOOL_SCHEMAS}
        for definition in canonical:
            raw = definition.to_default_dict()
            function = raw.get("function", raw)
            fallback = fallback_by_name[function["name"]]
            parameters = function.get("parameters") or {
                "properties": function.get("properties", {}),
                "required": function.get("required", []),
            }
            self.assertEqual(fallback["parameters"]["properties"], parameters["properties"])
            self.assertEqual(fallback["parameters"].get("required", []), parameters.get("required", []))
