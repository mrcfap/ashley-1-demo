"""Rastreabilidade de evidências de memória usadas no prompt.

Não atribui origem a fatos que não tenham metadados verificáveis.
Não grava dados pessoais adicionais nem expõe identificadores ao usuário.
"""
from datetime import datetime


def _data_segura(valor):
    if not valor:
        return "desconhecida"
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).isoformat()
    except (TypeError, ValueError):
        return "desconhecida"


def consulta_autobiografica(consulta):
    """Identifica pedidos amplos sobre a história pessoal sem capturar perguntas pontuais."""
    import re
    texto = " ".join(str(consulta or "").casefold().split())
    return bool(re.search(
        r"(?:fale|conte|diga|resuma|descreva|lembre).{0,45}"
        r"(?:sobre mim|de mim|minha historia|minha trajetória|"
        r"o que sabe sobre mim|informacoes que (?:te )?passei|"
        r"conversas anteriores)|"
        r"(?:quem sou eu|o que voce sabe sobre mim|"
        r"quais informacoes voce tem sobre mim)",
        texto
    ))


def contexto_rastreavel(memoria, user_id, consulta, limite=8):
    """Retorna apenas registros efetivamente encontrados na tabela persistente."""
    registros = (memoria.panorama_autobiografico(user_id, limite=max(limite, 24))
                 if consulta_autobiografica(consulta)
                 else memoria.buscar(user_id, consulta, limite=limite))
    if not registros:
        return "Nenhum registro estruturado recuperado da memória persistente."
    linhas = []
    for registro in registros:
        categoria = str(registro.get("categoria", "sem_categoria"))[:80]
        chave = str(registro.get("chave", "sem_chave"))[:100]
        conteudo = str(registro.get("conteudo", ""))[:1600]
        criado = _data_segura(registro.get("criado_em"))
        atualizado = _data_segura(registro.get("atualizado_em"))
        linhas.append(
            f"- [origem=memoria_persistente; categoria={categoria}; chave={chave}; "
            f"criado_em={criado}; atualizado_em={atualizado}] {conteudo}"
        )
    return "\n".join(linhas)


INSTRUCOES_RASTREABILIDADE = """
RASTREABILIDADE COGNITIVA DA MEMÓRIA:
- Somente itens explicitamente marcados origem=memoria_persistente foram
  recuperados da tabela estruturada de memória persistente nesta resposta.
- PERFIL AUTENTICADO vem do cadastro da conta, não da memória persistente.
- HISTÓRICO RECENTE DA CONTA vem das últimas interações armazenadas; não
  prova que um fato tenha sido consolidado como memória persistente.
- FATOS EPISÓDICOS e CONTEXTO DO ORQUESTRADOR podem conter informações de
  outros mecanismos; não atribua origem exata sem metadados explícitos.
- Não afirme ter consultado um registro que não aparece nas fontes fornecidas.
- Datas de criação/atualização são datas do registro, não necessariamente
  datas em que o fato ocorreu.
- Quando perguntarem a origem de uma lembrança, cite a fonte verificável
  ou diga 'não consigo confirmar a origem'.
- Nunca invente identificadores, datas, certeza, nem uma trilha de auditoria.
- Não exponha metadados internos ou detalhes íntimos espontaneamente;
  responda apenas o necessário para a solicitação do usuário.
"""
