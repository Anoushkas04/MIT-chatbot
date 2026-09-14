import unittest

from app.sentiment_engine import analyze_sentiment


class SentimentEngineTests(unittest.TestCase):
    def test_positive_content(self):
        result = analyze_sentiment("The response was helpful, clear, and excellent.")
        self.assertEqual(result["label"], "positive")
        self.assertGreater(result["score"], 0)

    def test_negative_content(self):
        result = analyze_sentiment("This is confusing and the delay is awful.")
        self.assertEqual(result["label"], "negative")
        self.assertLess(result["score"], 0)

    def test_negation_changes_polarity(self):
        result = analyze_sentiment("The instructions are not helpful.")
        self.assertEqual(result["label"], "negative")


if __name__ == "__main__":
    unittest.main()
