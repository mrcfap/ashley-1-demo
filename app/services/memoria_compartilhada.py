"""Lembretes explícitos de palavra-chave e número, isolado por conta."""
import re
import os
import unicodedata

from app.triad.persistencia import conectar
from app.services.memoria_episodica import responder_fato


def _normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold()) if not unicodedata.combining(c))


def responder_lembrete(usuario, mensagem):
    if os.getenv("DATABASE_URL"):
        from app.services.lembrete_postgres import responder
        resultado = responder(usuario, mensagem)
        if resultado is not None:
            return resultado
    fato = responder_fato(usuario, mensagem)
    if fato is not None:
        return fato
    texto = _normalizar(mensagem)
    palavra = bool(re.search(r'\bpalavra(?:[- ]chave)?\b', texto))
    numero = bool(re.search(r'\bnumero\b', texto))
    comando = re.search(r'\b(?:guarde|salve|registre|memorize|corrija|atualize)\b', texto)
    # Correções curtas como "Coloque Jaque em vez de Jack" referem-se à
    # palavra vigente da conta, mesmo sem repetir "palavra" no comando.
    correcao = re.search(r'^(?:coloque|troque|substitua|mude|corrija|atualize)\s+(.{1,80}?)\s+em\s+vez\s+de\s+(.{1,80})[.!?]?$', mensagem.strip(), re.I)
    historico = bool(palavra and re.search(r'\b(?:tres|3|historico|alteracoes|correcoes|versoes|sequencia)\b', texto))
    registro = None
    if correcao:
        novo, anterior = (v.strip(' \"“”.,!?') for v in correcao.groups())
        if not novo or not anterior:
            return 'Informe a palavra anterior e a nova palavra.'
        with conectar() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS triad_lembrete_conta (
                usuario TEXT PRIMARY KEY, palavra TEXT NOT NULL, numero TEXT NOT NULL
            )""")
            atual = conn.execute('SELECT palavra FROM triad_lembrete_conta WHERE usuario=?', (str(usuario),)).fetchone()
            if not atual or atual[0].casefold() != anterior.casefold():
                return 'Não alterei a palavra: o valor anterior informado não corresponde ao que está salvo.'
            _registrar_palavra(conn, usuario, novo)
        return f'Atualizei a palavra de “{anterior}” para “{novo}”.'
    if comando and (palavra or numero):
        original = re.search(r'["“]([^"”\r\n]{1,80})["”]', mensagem)
        algarismo = re.search(r'\bnumero\s*(?:agora\s+e\s+|e\s+|para\s+|:\s*)?(-?\d{1,18})(?!\w)', texto)
        valor_palavra = original[1].strip() if palavra and original else ''
        valor_numero = algarismo[1] if numero and algarismo else ''
        if palavra and not valor_palavra:
            return 'Diga a palavra que quer guardar entre aspas.'
        if numero and not valor_numero:
            return 'Informe o número que quer guardar.'
        registro = (valor_palavra, valor_numero)
    else:
        consulta = re.search(r'\b(?:qual|quais|lembra|recupere|diz|diga)\b', texto)
        refere_memoria = re.search(r'\b(?:guardar|guardei|salvei|memorizei|lembra|recupere|lembrete)\b', texto)
        indireta = bool((palavra or numero) and re.search(r"\b(?:lembra|lembrar|recorda|pedi|guardei)\b", texto))
        if not (((palavra or numero) and consulta and refere_memoria) or historico or indireta):
            return None

    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS triad_lembrete_conta (
            usuario TEXT PRIMARY KEY, palavra TEXT NOT NULL, numero TEXT NOT NULL
        )""")
        if registro:
            if palavra and registro[0]:
                _registrar_palavra(conn, usuario, registro[0])
            conn.execute("""INSERT INTO triad_lembrete_conta(usuario,palavra,numero) VALUES (?,?,?)
                ON CONFLICT(usuario) DO UPDATE SET
                palavra=COALESCE(NULLIF(excluded.palavra,''), triad_lembrete_conta.palavra),
                numero=COALESCE(NULLIF(excluded.numero,''), triad_lembrete_conta.numero)""",
                         (str(usuario), *registro))
            if palavra and numero:
                return f'Guardei na sua conta a palavra-chave “{registro[0]}” e o número {registro[1]}.'
            if palavra:
                return f'Guardei na sua conta a palavra “{registro[0]}”.'
            return f'Guardei na sua conta o número {registro[1]}.'
        salvo = conn.execute('SELECT palavra,numero FROM triad_lembrete_conta WHERE usuario=?',
                            (str(usuario),)).fetchone()
        if historico:
            _criar_historico(conn)
            valores = [r[0] for r in conn.execute(
                'SELECT valor FROM triad_lembrete_historico WHERE usuario=? ORDER BY id', (str(usuario),))]
            if not valores:
                return 'Não encontrei histórico de alterações da palavra nesta conta.'
            return ('A sequência registrada foi: ' + ' → '.join(valores) +
                    '. A palavra atual é “' + valores[-1] + '”.')
    valor_palavra, valor_numero = salvo or ('', '')
    if palavra and numero and valor_palavra and valor_numero:
        return f'A palavra-chave que você pediu para guardar é “{valor_palavra}” e o número é {valor_numero}.'
    respostas = []
    if palavra:
        respostas.append(f'A palavra que você pediu para guardar é “{valor_palavra}”.'
                         if valor_palavra else 'Ainda não encontrei uma palavra guardada nesta conta.')
    if numero:
        respostas.append(f'O número que você pediu para guardar é {valor_numero}.'
                         if valor_numero else 'Ainda não encontrei um número guardado nesta conta.')
    return ' '.join(respostas)


def _criar_historico(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS triad_lembrete_historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT NOT NULL,
        valor TEXT NOT NULL, registrado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )""")


def _registrar_palavra(conn, usuario, valor):
    _criar_historico(conn)
    anterior = conn.execute('SELECT valor FROM triad_lembrete_historico WHERE usuario=? ORDER BY id DESC LIMIT 1',
                            (str(usuario),)).fetchone()
    if not anterior or anterior[0] != valor:
        conn.execute('INSERT INTO triad_lembrete_historico(usuario,valor) VALUES (?,?)', (str(usuario), valor))
    conn.execute("""INSERT INTO triad_lembrete_conta(usuario,palavra,numero) VALUES (?,?,'')
        ON CONFLICT(usuario) DO UPDATE SET palavra=excluded.palavra""", (str(usuario), valor))
