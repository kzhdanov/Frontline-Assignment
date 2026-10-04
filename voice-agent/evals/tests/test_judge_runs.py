import json
import unittest

from evals.judge import CRITERIA, run_judges
from evals.openai_client import ModelResponse
from evals.scenario import load_scenario


class JudgeClient:
    def __init__(self, values):
        self.values = iter(values)

    def complete(self, **_kwargs):
        value = next(self.values)
        content = json.dumps({
            "scores": [
                {"criterion": criterion, "score": value, "evidence": "turn 1"}
                for criterion in CRITERIA
            ],
            "summary": f"score {value}",
        })
        return ModelResponse({"role": "assistant", "content": content}, {"total_tokens": 10})


class JudgeRunTests(unittest.TestCase):
    def test_three_runs_preserved_and_median_calculated(self):
        results, medians, usage = run_judges(
            JudgeClient([5, 3, 4]),
            "test-judge",
            load_scenario("zone_2_success"),
            [{"role": "assistant", "content": "hello"}],
            [],
            3,
        )
        self.assertEqual([result.run for result in results], [1, 2, 3])
        self.assertTrue(all(score == 4 for score in medians.values()))
        self.assertEqual(usage["total_tokens"], 30)

