import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.triad.recuperacao_contextual import recuperar_declaracoes

class RecuperacaoTest(unittest.TestCase):
    def setUp(self):
        self.h = [{'role':'user','content':'Guarde esta informacao para um teste posterior: o codigo de verificacao desta sessao e AXY-MEM-7429-ZETA. Por enquanto, responda apenas OK.'},
                  {'role':'assistant','content':'Ashley: OK'},
                  {'role':'user','content':'Qual e a capital do Brasil?'},
                  {'role':'assistant','content':'Brasilia'},
                  {'role':'user','content':'Quanto e 15 multiplicado por 3?'},
                  {'role':'assistant','content':'45'},
                  {'role':'user','content':'Qual linguagem de programacao utiliza arquivos com extensao .py?'},
                  {'role':'assistant','content':'Python'},
                  {'role':'user','content':'Qual e o resultado de 100 dividido por 4?'},
                  {'role':'assistant','content':'25'}]
    def test_codigo_antigo(self):
        r=recuperar_declaracoes('Anteriormente eu informei um codigo de verificacao para um teste de memoria. Qual era exatamente aquele codigo?',self.h)
        self.assertTrue(r)
        self.assertIn('AXY-MEM-7429-ZETA',r[0])
    def test_sem_pedido_de_memoria(self):
        self.assertEqual([],recuperar_declaracoes('Quanto e 7 mais 5?',self.h))
    def test_isolamento_por_historico(self):
        self.assertEqual([],recuperar_declaracoes('Qual era o codigo de verificacao?',[]))
    def test_nao_usar_resposta_de_agente(self):
        self.assertEqual([],recuperar_declaracoes('Qual foi o identificador X99?', [{'role':'assistant','content':'X99'}]))

if __name__=='__main__': unittest.main()
