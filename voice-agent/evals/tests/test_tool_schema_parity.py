import unittest

from tool_contracts import TOOL_CONTRACTS
from evals.simulated_tools import TOOL_SCHEMAS


class ToolSchemaParityTests(unittest.TestCase):
    def test_evaluator_schemas_are_derived_from_canonical_contracts(self):
        for item in TOOL_SCHEMAS:
            function = item["function"]
            contract = TOOL_CONTRACTS[function["name"]]
            self.assertEqual(function["description"], contract["description"])
            self.assertEqual(function["parameters"]["properties"], contract["properties"])
            self.assertEqual(function["parameters"]["required"], contract["required"])
