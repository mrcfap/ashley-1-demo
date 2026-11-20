# Script de aplicação conservadora: insere método somente se estiver ausente.
from pathlib import Path
p = Path('app/memory/memoria_longa.py')
s = p.read_text(encoding='utf-8')
if 'def contexto_recente(' in s:
    print('contexto_recente já existe; nenhuma alteração realizada.')
    raise SystemExit(0)
needle = '    def estatisticas(self, user_id):'
if s.count(needle) != 1:
    raise SystemExit('Não foi possível localizar ponto único de inserção; nenhuma alteração.')
method = '''    def contexto_recente(self, user_id, limite=4):
        """Retorna as últimas interações do usuário em ordem cronológica."""
        limite = max(1, min(int(limite), 20))
        with self._conn() as c:
            rows = c.execute("""
                SELECT entrada, resposta FROM interacoes_longo_prazo
                WHERE user_id=? ORDER BY id DESC LIMIT ?
            """, (user_id, limite)).fetchall()
        if not rows:
            return ""
        conversas = []
        for row in reversed(rows):
            entrada, resposta = row[0], row[1]
            conversas.append(f"Usuário: {str(entrada)[:1500]}\\nAshley: {str(resposta)[:2500]}")
        return "\\n\\n".join(conversas)

'''
backup = p.with_suffix('.py.backup_antes_contexto_recente')
backup.write_text(s, encoding='utf-8')
p.write_text(s.replace(needle, method + needle), encoding='utf-8')
print('Método contexto_recente adicionado. Backup:', backup)
