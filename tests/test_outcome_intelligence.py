import tempfile
import unittest
from pathlib import Path
from app.future.outcome_intelligence import OutcomeEvent, OutcomeTracker

class OutcomeTests(unittest.TestCase):
    def test_consent_and_evidence(self):
        with self.assertRaises(PermissionError):
            OutcomeEvent("g", "tempo", 10).validate()
        with self.assertRaises(ValueError):
            OutcomeEvent("g", "tempo", 10, 8, approved=True).validate()

    def test_outcome_metrics(self):
        with tempfile.TemporaryDirectory() as d:
            tracker = OutcomeTracker(Path(d)/"events.jsonl")
            tracker.record(OutcomeEvent("g", "tempo", 10, 8, "ticket-1", True))
            tracker.record(OutcomeEvent("g", "tempo", 10, 6, "ticket-2", True))
            self.assertEqual(tracker.summary("g")["mean_absolute_error"], 3)
            self.assertEqual(tracker.summary("other")["observations"], 0)

if __name__ == "__main__": unittest.main()
