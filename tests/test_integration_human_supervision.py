import unittest
# Isola métodos reais por AST para testar integração sem carregar provedores externos.
import ast
from pathlib import Path
source = Path(__file__).resolve().parents[1] / "app/core/orquestrador.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "OrquestradorAshley")
methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in ("avaliar_fundacao_humana", "avaliar_decisao_supervisionada")]
assert len(methods) == 2
module = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name="OrquestradorAshley", bases=[], keywords=[], body=methods, decorator_list=[])], type_ignores=[]))
namespace = {}
exec(compile(module, str(source), "exec"), namespace)
OrquestradorAshley = namespace["OrquestradorAshley"]

class IntegrationHumanSupervisionTests(unittest.TestCase):
    def setUp(self):
        self.orch = OrquestradorAshley.__new__(OrquestradorAshley)

    def test_consent_is_required(self):
        r = self.orch.avaliar_fundacao_humana(owner_id="u1", values=[], limits={}, mode="conversa", options=[], consent=False)
        self.assertEqual(r["status"], "CONSENT_REQUIRED")
        self.assertFalse(r["execution_authorized"])

    def test_human_review_detects_conflict(self):
        r = self.orch.avaliar_fundacao_humana(owner_id="u1", values=["saude"], limits={"horas":8}, mode="reflexao", options=[{"name":"A","metrics":{"horas":12}}], consent=True)
        self.assertFalse(r["execution_authorized"])
        self.assertEqual(r["essentia"][0]["status"], "REVIEW_REQUIRED")
        self.assertEqual(r["elo"]["mode"], "reflexao")

    def test_parallax_needs_review_without_assessments(self):
        r = self.orch.avaliar_decisao_supervisionada(proposal={"objective":"teste"}, assessments={})
        self.assertEqual(r["recommendation"], "HUMAN_REVIEW")
        self.assertFalse(r["automatic_execution"])

if __name__ == "__main__": unittest.main()
