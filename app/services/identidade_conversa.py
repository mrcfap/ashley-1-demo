"""Responde perguntas de identidade com dados explícitos da conversa ou conta."""
import re
import unicodedata


PERGUNTA_NOME = re.compile(
    r'^(?:(?:ashley|ashen)[, ]+)?(?:quem sou eu|qual (?:e )?o meu nome|como me chamo|voce lembra (?:d[eo] )?meu nome)[?!. ]*$'
)
PERGUNTA_INICIO = re.compile(
    r'^(?:(?:ashley|ashen)[, ]+)?(?:eu )?(?:falei|disse) (?:la )?no (?:inicio|comeco) da (?:nossa )?(?:conversa|interacao)[?!. ]*$'
)
LEMBRETE_MEMORIA = re.compile(
    r'^(?:(?:ashley|ashen)[, ]+)?(?:eu )?(?:falei|disse) (?:o )?meu nome\b.*\b(?:sua memoria|seu problema de memoria)\b', re.S
)
NOME_DECLARADO = re.compile(
    r'^\s*(?:(?:ashley|ashen)[, ]+)?(?:aqui (?:é|e) (?:o |a )?|meu nome (?:é|e) |eu me chamo |me chamo )'
    r'(?P<nome>[^\W\d_]+(?:[-’\'][^\W\d_]+)*(?: +[^\W\d_]+(?:[-’\'][^\W\d_]+)*){0,3})'
    r'(?=[,.!?;:\n]|$|\s+(?:e|sou)\s)', re.I,
)


def _normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold()) if not unicodedata.combining(c))


def responder_identidade(mensagem, historico, nome_cadastrado):
    consulta = _normalizar(mensagem.strip())
    inicio = PERGUNTA_INICIO.fullmatch(consulta)
    lembrete = LEMBRETE_MEMORIA.match(consulta)
    if not (PERGUNTA_NOME.fullmatch(consulta) or inicio or lembrete):
        return None
    declaracoes = []
    for item in historico:
        if item.get('role') == 'user':
            match = NOME_DECLARADO.match(item.get('content', ''))
            if match:
                nome = re.split(r'\s+(?:e|sou)\s+', match['nome'], maxsplit=1, flags=re.I)[0]
                declaracoes.append(nome)
    if declaracoes:
        nome = declaracoes[0] if inicio else declaracoes[-1]
        if lembrete:
            return f'Você se apresentou como {nome}. Entendi que você está falando da minha memória e quer corrigir como eu recupero seu nome.'
        return f'Você se apresentou como {nome} nesta conversa.'
    if nome_cadastrado:
        return f'Pelo cadastro da sua conta, seu nome é {nome_cadastrado}.'
    return 'Não encontrei seu nome no histórico disponível desta conversa nem no cadastro da conta.'
