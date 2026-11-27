"""Registro e retomada de pendências operacionais pelo chat."""

from datetime import date, datetime, timedelta
import re
from zoneinfo import ZoneInfo

from app.tasks.motor_execucao_v22 import ESTADOS_FINAIS, MotorExecucaoV22

_REGISTRO = re.compile(r"registrar pendência:\s*([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)", re.I)
_RETOMADA = re.compile(r"retomar (pendência|pendiente)\s+([0-9a-f-]{36})", re.I)
_TRANSFERENCIA = re.compile(r"(transferir|aceitar) pendência\s+([0-9a-f-]{36})\s*\|\s*([1-9][0-9]{0,17})", re.I)
_PRAZOS_RELATIVOS = {"hoje": 0, "amanhã": 1}
_ESTADOS_ES = {
    "AGUARDANDO_APROVACAO": "A la espera de aprobación",
    "AGENDADA": "Programada",
    "PENDENTE": "Pendiente",
    "EXECUTANDO": "En ejecución",
    "CONCLUIDA": "Completada",
    "CANCELADA": "Cancelada",
    "FALHOU": "Fallida",
}


def responder_passagem_turno(db, usuario, mensagem, *, hoje=None):
    mensagem = mensagem.strip()
    registro = _REGISTRO.fullmatch(mensagem)
    retomada = _RETOMADA.fullmatch(mensagem)
    transferencia = _TRANSFERENCIA.fullmatch(mensagem)
    if not registro and not retomada and not transferencia:
        return None

    fila = MotorExecucaoV22(db)
    if transferencia:
        comando, tarefa_id, conta = transferencia.groups()
        aceitar = comando.casefold() == "aceitar"
        titular, destinatario = (int(conta), usuario) if aceitar else (usuario, int(conta))
        if not fila.transferir_passagem(tarefa_id.lower(), titular, destinatario, aceitar=aceitar):
            return "Não consegui confirmar essa transferência.", "pt-BR"
        resposta = "Transferência aceita." if aceitar else "Transferência aguardando aceite."
        return resposta, "pt-BR"

    hoje = hoje or datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    if registro:
        titulo, responsavel, prazo, origem = map(str.strip, registro.groups())
        if not all((titulo, responsavel, prazo, origem)):
            return "Preencha a pendência, o responsável, o prazo e a origem.", "pt-BR"
        dias = _PRAZOS_RELATIVOS.get(prazo.casefold())
        try:
            data = date.fromisoformat(prazo) if dias is None else hoje + timedelta(days=dias)
        except ValueError:
            return "Informe o prazo como AAAA-MM-DD, hoje ou amanhã.", "pt-BR"
        tarefa = fila.criar(
            user_id=usuario, titulo=titulo, objetivo=titulo, requer_aprovacao=True,
            metadados={"tipo": "passagem_turno", "responsavel": responsavel,
                       "prazo": data.isoformat(), "origem": origem},
        )
        resposta = f"Pendência registrada com prazo em {data.isoformat()}. Identificador: {tarefa['id']}"
        espanhol = False
    else:
        espanhol = retomada[1].casefold() == "pendiente"
        tarefa = fila.obter(retomada[2].lower(), usuario)
        if not tarefa or tarefa["metadados"].get("tipo") != "passagem_turno":
            return ("No encontré esa tarea.", "es-ES") if espanhol else ("Não encontrei essa pendência.", "pt-BR")
        dados = tarefa["metadados"]
        estado = tarefa["status"]
        if espanhol:
            resposta = (f"{tarefa['titulo']}. Responsable: {dados['responsavel']}. "
                        f"Plazo: {dados['prazo']}. Origen: {dados['origem']}. {_ESTADOS_ES.get(estado, estado)}.")
        else:
            rotulo = "Aguardando aprovação" if estado == "AGUARDANDO_APROVACAO" else estado.capitalize()
            resposta = (f"{tarefa['titulo']}. Responsável: {dados['responsavel']}. "
                        f"Prazo: {dados['prazo']}. Origem: {dados['origem']}. {rotulo}.")

    vencidas = 0
    for item in fila.listar(usuario, limite=-1):
        dados = item["metadados"]
        if dados.get("tipo") != "passagem_turno" or item["status"] in ESTADOS_FINAIS:
            continue
        try:
            vencidas += date.fromisoformat(dados.get("prazo", "")) < hoje
        except (ValueError, TypeError):
            continue
    if vencidas:
        aviso = "Pendientes con plazo vencido" if espanhol else "Pendências com prazo vencido"
        resposta += f"\n{aviso}: {vencidas}."
    return resposta, "es-ES" if espanhol else "pt-BR"
