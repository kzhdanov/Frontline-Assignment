import json
import unittest

from evals.judge import CRITERIA, _parse_result
from evals.openai_client import ModelError


class JudgeParserTests(unittest.TestCase):
    def test_parse_complete_judge_result(self):
        content = json.dumps({
            "scores": [{"criterion": name, "score": 4, "evidence": "turn 1"} for name in CRITERIA],
            "summary": "Good run",
        })
        result = _parse_result(1, content)
        self.assertEqual(len(result.scores), len(CRITERIA))
        self.assertTrue(all(score.score == 4 for score in result.scores))

    def test_parse_rejects_missing_criterion(self):
        content = json.dumps({"scores": [{"criterion": CRITERIA[0], "score": 4, "evidence": "turn 1"}]})
        with self.assertRaises(ModelError):
            _parse_result(1, content)
