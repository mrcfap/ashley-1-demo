import os, tempfile, unittest, sqlite3
from contextlib import closing
from unittest.mock import patch
from app.memory.memoria_longa import MemoriaLongoPrazo
class MemoriaInicializacao(unittest.TestCase):
    def test_postgres_nao_conecta_no_construtor(self):
        with patch.dict(os.environ, {'DATABASE_URL':'postgresql://invalid'}, clear=False):
            m=MemoriaLongoPrazo('unused.db')
            self.assertFalse(m._postgres_inicializado)
    def test_sqlite_fecha_conexao_apos_uso(self):
        with patch.dict(os.environ, {'DATABASE_URL': ''}, clear=False):
            with tempfile.TemporaryDirectory() as d:
                db = os.path.join(d, 'memoria.db')
                m = MemoriaLongoPrazo(db)
                m.guardar(1, 'teste', 'chave', 'valor')
                self.assertEqual(m.estatisticas(1)['memorias'], 1)
                # Deve ser possível abrir uma conexão exclusiva depois do uso.
                with closing(sqlite3.connect(db, timeout=1)) as conn:
                    conn.execute('BEGIN EXCLUSIVE')
                    conn.execute('ROLLBACK')

    def test_sqlite_guarda_e_recupera(self):
        with patch.dict(os.environ, {'DATABASE_URL':''}, clear=False):
            with tempfile.TemporaryDirectory() as d:
                m=MemoriaLongoPrazo(os.path.join(d,'memoria.db'))
                m.guardar(1,'teste','chave','valor')
                self.assertEqual(m.buscar(1)[0]['conteudo'],'valor')
                self.assertEqual(m.buscar(2),[])
if __name__=='__main__':unittest.main()
