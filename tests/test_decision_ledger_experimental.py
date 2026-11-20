"""Testes isolados do ledger experimental (sem dependências externas)."""
import tempfile
import unittest
from pathlib import Path
from app.governance.decision_ledger import DecisionLedger, LedgerIntegrityError


class TestDecisionLedger(unittest.TestCase):
    def test_chain_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            ledger = DecisionLedger(path)
            ledger.record(case_id="c1", decision="revisar", evidence_refs=["doc:1"])
            ledger.record(case_id="c1", decision="aprovar", evidence_refs=["doc:1"], approved_by="operador", status="approved")
            self.assertEqual(ledger.verify()["count"], 2)
            path.write_text(path.read_text().replace("revisar", "alterado"), encoding="utf-8")
            with self.assertRaises(LedgerIntegrityError):
                ledger.verify()

    def test_approval_required(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = DecisionLedger(Path(directory) / "ledger.jsonl")
            with self.assertRaises(ValueError):
                ledger.record(case_id="c1", decision="executar", evidence_refs=[], status="executed")


if __name__ == "__main__":
    unittest.main()
