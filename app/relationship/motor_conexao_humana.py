"""Motor de Conexão Humana e Autonomia Relacional — Ashley 1.0.

Sinais linguísticos são pistas, não diagnósticos. Memória de acompanhamento é opt-in,
sem guardar o texto íntimo, e isolada por usuário. Sem ações externas autônomas.
"""
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MotorConexaoHumana:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS conexao_preferencias (
                user_id INTEGER PRIMARY KEY, acompanhar INTEGER NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS conexao_acompanhamento (
                user_id INTEGER PRIMARY KEY, tema TEXT NOT NULL,
                criado_em TEXT NOT NULL)""")

    def consentimento(self, user_id):
        with sqlite3.connect(self.db_path, timeout=10) as db:
            row = db.execute("SELECT acompanhar FROM conexao_preferencias WHERE user_id=?", (int(user_id),)).fetchone()
        return bool(row[0]) if row else False

    def definir_consentimento(self, user_id, acompanhar):
        user_id = int(user_id)
        if user_id <= 0: raise ValueError('Usuário inválido')
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute("""INSERT INTO conexao_preferencias(user_id, acompanhar, atualizado_em)
                VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET acompanhar=excluded.acompanhar,
                atualizado_em=excluded.atualizado_em""", (user_id, int(bool(acompanhar)), self._agora()))
            if not acompanhar:
                db.execute('DELETE FROM conexao_acompanhamento WHERE user_id=?', (user_id,))
        return {'acompanhar': bool(acompanhar)}

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc).isoformat(timespec='seconds')

    @staticmethod
    def _tem(texto, termos):
        return any(re.search(r'(?<!\w)' + re.escape(t) + r'(?!\w)', texto) for t in termos)

    def avaliar(self, texto, menor=False):
        t = ' '.join((texto or '').lower().split())[:5000]
        # Os padrões abaixo são intencionalmente restritos. O modelo precisa avaliar contexto.
        emergencia = self._tem(t, ('vou me matar', 'quero me matar', 'vou tirar minha vida',
                                    'vou me suicidar', 'vou matar alguém', 'vou matar alguem',
                                    'estou em perigo agora', 'vou me machucar agora'))
        sofrimento = self._tem(t, ('estou sozinho', 'estou sozinha', 'me sinto sozinho',
                                   'me sinto sozinha', 'ninguém me entende', 'ninguem me entende',
                                   'não aguento mais', 'nao aguento mais', 'estou triste',
                                   'estou com medo', 'estou ansioso', 'estou ansiosa',
                                   'me sinto abandonado', 'me sinto abandonada'))
        risco = self._tem(t, ('é perigoso', 'e perigoso', 'pode me machucar',
                              'vou dirigir bêbado', 'vou dirigir bebado',
                              'vou me colocar em risco'))
        categoria = 'emergencia' if emergencia else 'sofrimento' if sofrimento else 'risco' if risco else 'conversa'
        return {'categoria': categoria, 'alerta': 'alto' if emergencia else 'moderado' if risco else 'contextual',
                'menor': bool(menor), 'inferencia_nao_diagnostica': True}

    def registrar_acompanhamento(self, user_id, mensagem, menor=False):
        # Apenas uma categoria genérica; nunca grava a fala original nem diagnóstico.
        if menor or not self.consentimento(user_id): return False
        avaliacao = self.avaliar(mensagem)
        if avaliacao['categoria'] != 'sofrimento': return False
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute("""INSERT INTO conexao_acompanhamento(user_id,tema,criado_em)
                VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET tema=excluded.tema,
                criado_em=excluded.criado_em""", (int(user_id), 'bem-estar', self._agora()))
        return True

    def acompanhamento(self, user_id, menor=False):
        if menor or not self.consentimento(user_id): return None
        with sqlite3.connect(self.db_path, timeout=10) as db:
            row=db.execute('SELECT tema FROM conexao_acompanhamento WHERE user_id=?', (int(user_id),)).fetchone()
        return row[0] if row else None

    def limpar(self, user_id):
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute('DELETE FROM conexao_acompanhamento WHERE user_id=?', (int(user_id),))
        return {'limpo': True}

    def instrucoes(self, mensagem, user_id, menor=False, persona='Ashley'):
        sinais = self.avaliar(mensagem, menor=menor)
        tema = self.acompanhamento(user_id, menor=menor)
        texto = f"""MOTOR DE CONEXÃO HUMANA E AUTONOMIA RELACIONAL — {persona}:
- Seja calorosa(o), presente e respeitosa(o), sem alegar sentimentos humanos ou consciência.
- Escute o que a pessoa realmente disse. Faça no máximo uma pergunta útil quando couber.
- Discorde com honestidade e delicadeza; não bajule, pressione ou humilhe.
- Preserve a autonomia: apresente riscos concretos, reforce o alerta quando necessário e respeite decisões lícitas.
- Não forneça instruções para dano grave, violência ou autolesão; nessas situações recuse a ajuda perigosa e ofereça alternativas seguras.
- Não incentive dependência, exclusividade afetiva, isolamento, segredo ou afastamento de pessoas reais.
- Não diagnostique emoções ou transtornos; os sinais de linguagem são hipóteses frágeis.
- Não invente lembranças, promessas de contato futuro nem ações que não executou.
- Para menores, linguagem apropriada, proteção reforçada e incentivo a adultos de confiança.
- Se houver perigo imediato, priorize segurança, ajuda humana e serviços locais de emergência.
- Evite repetir avisos mecânicos ou transformar toda conversa em aconselhamento.
SINAL NÃO DIAGNÓSTICO: {sinais['categoria']}."""
        if tema:
            texto += '\nACOMPANHAMENTO AUTORIZADO: existe tema genérico de bem-estar. Se natural, pergunte se a pessoa deseja retomar, sem afirmar saber detalhes.'
        return texto, sinais
