import unittest
from app.integracao_v48_v61 import inventario_v48_v61, orientacao_v59, politica_recuperacao_v55

class TestIntegracao(unittest.TestCase):
    def test_importacao(self):
        resultado=inventario_v48_v61()
        self.assertEqual(len(resultado['motores']),14)
        self.assertTrue(all(x['importavel'] for x in resultado['motores'].values()),resultado)
    def test_orientacao_comum(self):
        self.assertEqual(orientacao_v59('bom dia'), '')
    def test_orientacao_ansiedade(self):
        self.assertIn('NEUROPSYCHE',orientacao_v59('estou com ansiedade'))
    def test_protecao_menor(self):
        self.assertIn('NEUROPSYCHE',orientacao_v59('estou sozinho',menor=True))
    def test_sem_retry_automatico(self):
        self.assertEqual(politica_recuperacao_v55('temporary_unavailable')['action'],'manual_review')

if __name__=='__main__':unittest.main()
