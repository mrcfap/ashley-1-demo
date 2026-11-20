import unittest
from app.vision.eventos_presenca import EventosPresenca

class TestEventosPresenca(unittest.TestCase):
    def test_confirmacao_e_saida(self):
        e=EventosPresenca()
        self.assertEqual(e.observar('a',1,True,True),[])
        self.assertEqual([x['tipo'] for x in e.observar('a',1,True,True)],['presenca_detectada','convite_conversa'])
        self.assertEqual(e.observar('a',1,True,True),[])
        for _ in range(2): self.assertEqual(e.observar('a',0,True,True),[])
        self.assertEqual(e.observar('a',0,True,True)[0]['tipo'],'ambiente_sem_pessoas')
    def test_sem_consentimento(self):
        e=EventosPresenca(quadros_confirmacao=1)
        self.assertEqual(e.observar('a',1,False,True),[])
        self.assertEqual([x['tipo'] for x in e.observar('a',1,True,False)],['presenca_detectada'])
        self.assertEqual(e.observar('a',1,False,True),[])
    def test_sem_repeticao_rapida(self):
        t=[1000]
        e=EventosPresenca(quadros_confirmacao=1,quadros_saida=1,relogio=lambda:t[0])
        self.assertEqual(len(e.observar('a',1,True,True)),2)
        e.observar('a',0,True,True)
        self.assertEqual(len(e.observar('a',1,True,True)),1)
        t[0]+=301
        e.observar('a',0,True,True)
        self.assertEqual(len(e.observar('a',1,True,True)),2)

if __name__=='__main__': unittest.main()
