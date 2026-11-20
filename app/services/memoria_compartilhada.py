"""Lembretes explícitos de palavra-chave e número, isolado por conta."""
import re
import unicodedata

from app.triad.persistencia import conectar
from app.services.memoria_episodica import responder_fato


def _normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold()) if not unicodedata.combining(c))


def responder_lembrete(usuario, mensagem):
    fato = responder_fato(usuario, mensagem)
    if fato is not None:
        return fato
    texto = _normalizar(mensagem)
    palavra = bool(re.search(r'\bpalavra(?:[- ]chave)?\b', texto))
    numero = bool(re.search(r'\bnumero\b', texto))
    comando = re.search(r'\b(?:guarde|salve|registre|memorize|corrija|atualize)\b', texto)
    registro = None
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
        if not ((palavra or numero) and consulta and refere_memoria):
            return None

    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS triad_lembrete_conta (
            usuario TEXT PRIMARY KEY, palavra TEXT NOT NULL, numero TEXT NOT NULL
        )""")
        if registro:
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
