import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.operations.runtime import runtime_report, mission_report


class RuntimeTests(unittest.TestCase):
    def test_report_does_not_create_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = runtime_report(root)
            self.assertFalse(report['production_ready'])
            self.assertEqual(report['mode'], 'read_only')
            self.assertEqual(list(root.iterdir()), [])

    def test_missing_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(mission_report(Path(tmp) / 'missing.db', 1)['available'])
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_user_isolation_and_no_sensitive_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'tasks.db'
            conn = sqlite3.connect(db)
            try:
                conn.execute('CREATE TABLE tarefas_v22 (id TEXT, user_id INTEGER, titulo TEXT, objetivo TEXT, status TEXT, progresso INTEGER, etapa_atual TEXT, criado_em TEXT, atualizado_em TEXT, requer_aprovacao INTEGER, aprovado INTEGER)')
                conn.executemany('INSERT INTO tarefas_v22 VALUES (?,?,?,?,?,?,?,?,?,?,?)', [
                    ('a', 1, 'Tarefa 1', 'segredo um', 'PENDENTE', 0, 'planejamento', '2026', '2026', 1, 0),
                    ('b', 2, 'Tarefa 2', 'segredo dois', 'CONCLUIDA', 100, 'final', '2026', '2026', 0, 1),
                ])
                conn.commit()
            finally:
                conn.close()

            r = mission_report(db, 1)
            self.assertEqual([t['id'] for t in r['tasks']], ['a'])
            self.assertNotIn('objetivo', r['tasks'][0])

            # Encerrar explicitamente a conexão para liberar o arquivo no Windows.
            verify_conn = sqlite3.connect(db)
            try:
                count = verify_conn.execute('SELECT COUNT(*) FROM tarefas_v22').fetchone()[0]
            finally:
                verify_conn.close()
            self.assertEqual(count, 2)

    def test_invalid_user(self):
        with self.assertRaises(ValueError):
            mission_report('x.db', 0)


if __name__ == '__main__':
    unittest.main()
