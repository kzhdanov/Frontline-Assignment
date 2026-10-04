import unittest

from evals.amounts import extract_rate_amounts


class AmountExtractionTests(unittest.TestCase):
    def test_common_spoken_and_written_rates(self):
        examples = {
            "I can offer $2,000.": 2000,
            "My rate is USD 2000.": 2000,
            "I need 2000 dollars.": 2000,
            "I can do two thousand.": 2000,
            "Our maximum is nineteen hundred.": 1900,
            "I can do nine hundred fifty dollars.": 950,
        }
        for text, expected in examples.items():
            with self.subTest(text=text):
                self.assertIn(expected, extract_rate_amounts(text))

    def test_ids_dates_and_phones_are_not_rates(self):
        text = "Load 1001 picks up October 6 2026. Call 12025550147."
        self.assertEqual(extract_rate_amounts(text), [])
