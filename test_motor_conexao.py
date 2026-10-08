import tempfile
import unittest
from pathlib import Path
from app.relationship.motor_conexao_humana import MotorConexaoHumana

class TestMotorConexao(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.motor=MotorConexaoHumana(Path(self.tmp.name)/'test.db')
    def tearDown(self): self.tmp.cleanup()
    def test_sem_consentimento(self):
        self.assertFalse(self.motor.registrar_acompanhamento(1,'estou sozinho'))
        self.assertIsNone(self.motor.acompanhamento(1))
    def test_consentimento_isolamento_exclusao(self):
        self.motor.definir_consentimento(1,True)
        self.assertTrue(self.motor.registrar_acompanhamento(1,'estou sozinho'))
        self.assertEqual(self.motor.acompanhamento(1),'bem-estar')
        self.assertIsNone(self.motor.acompanhamento(2))
        self.motor.limpar(1)
        self.assertIsNone(self.motor.acompanhamento(1))
    def test_desativar_apaga(self):
        self.motor.definir_consentimento(1,True)
        self.motor.registrar_acompanhamento(1,'estou triste')
        self.motor.definir_consentimento(1,False)
        self.assertIsNone(self.motor.acompanhamento(1))
    def test_menor_nao_registra(self):
        self.motor.definir_consentimento(1,True)
        self.assertFalse(self.motor.registrar_acompanhamento(1,'estou triste',menor=True))
    def test_sinais_nao_diagnosticos(self):
        self.assertEqual(self.motor.avaliar('Quero me matar')['categoria'],'emergencia')
        self.assertEqual(self.motor.avaliar('Hoje foi bom')['categoria'],'conversa')
        self.assertIn('não diagnostique',self.motor.instrucoes('oi',1)[0].lower())

if __name__=='__main__': unittest.main()
