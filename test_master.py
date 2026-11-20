import unittest
from orquestrador_tudo_ligado import OrquestradorTudoLigado
class TestMaster(unittest.TestCase):
    def test_status_nao_finge_homologacao(self):
        s = OrquestradorTudoLigado().status_completo()
        self.assertFalse(s["todos_homologados"])
        self.assertEqual(s["status"], "integracao_em_validacao")
    def test_chat_sem_legado_falha_explicitamente(self):
        with self.assertRaises(RuntimeError):
            OrquestradorTudoLigado().processar("oi")
if __name__ == "__main__": unittest.main()
