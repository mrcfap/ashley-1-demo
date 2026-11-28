"""Explicit chat follow-up using the existing V4/V5 case engines."""
import re
from uuid import uuid4

from app.cases.database import case_connection


COMMANDS = {
    '/acompanhar', '/resultado', '/confirmar-resultado',
    '/aprovar-ajuste', '/desfazer-ajuste', '/retomar-caso', '/experiencias',
}
REPORT = re.compile(
    r'^(?:fiz|segui|testei) (?:o que voc[eê] (?:sugeriu|recomendou)|'
    r'(?:a|sua) (?:recomendaç[aã]o|sugest[aã]o))(?:\b|[,:])', re.I
)
ADJUSTMENTS = {
    'FALHA': 'Rever a hipótese por trás da recomendação e testar uma alternativa em pequena escala, usando o mesmo critério de sucesso.',
    'PARCIAL': 'Preservar o que funcionou, isolar o ponto que faltou e testar um ajuste usando o mesmo critério de sucesso.',
    'INCONCLUSIVO': 'Coletar uma observação verificável segundo o critério original antes de mudar a recomendação.',
}


def _find(conn, user, token):
    return conn.execute(
        'SELECT * FROM caso_retorno_chat WHERE user_id=? AND token=?', (user, token)
    ).fetchone()


def _case(conn, user, case_id):
    return conn.execute("""
        SELECT f.*, a.descricao, a.status AS action_status, p.criterio_sucesso, c.status AS case_status
        FROM caso_retorno_chat f
        JOIN caso_proximas_acoes a ON a.id=f.acao_id AND a.user_id=f.user_id AND a.caso_id=f.caso_id
        JOIN casos c ON c.id=f.caso_id AND c.user_id=f.user_id
        LEFT JOIN caso_planos p ON p.caso_id=c.id AND p.user_id=c.user_id AND p.status='ATIVO'
        WHERE f.user_id=? AND f.caso_id=?
    """, (user, case_id)).fetchone()


def _start(conn, oq, user, argument):
    action, sep, criterion = map(str.strip, argument.partition('|'))
    if not sep or not action or not criterion or max(len(action), len(criterion)) > 1500:
        return 'Use /acompanhar ação recomendada | critério de sucesso (até 1.500 caracteres por campo).'
    case = oq.motor_casos.criar_caso(user, action[:100], action, criterion, connection=conn)
    case_id = case['id']
    oq.motor_resolucao.criar_plano(case_id, user, criterion, action, criterion, connection=conn)
    action_id = oq.definir_proxima_acao_caso(case_id, action, connection=conn)
    conn.execute('INSERT INTO caso_retorno_chat(caso_id,user_id,acao_id) VALUES (?,?,?)',
                 (case_id, user, action_id))
    return (f'Caso #{case_id} registrado. A recomendação é: {action}\n'
            f'Critério de sucesso: {criterion}\n'
            f'Quando testar, use /resultado {case_id} SUCESSO|PARCIAL|FALHA|INCONCLUSIVO seguido do que aconteceu. Escolha uma das quatro classificações.')


def _stage(conn, user, case, classification, report):
    if not case or case['case_status'] in ('RESOLVIDO', 'ARQUIVADO') or case['action_status'] != 'PENDENTE' or case['estado'] not in ('aberto', 'pendente'):
        return 'Não encontrei uma recomendação pendente para esse caso na sua conta.'
    token = uuid4().hex[:12]
    conn.execute("""UPDATE caso_retorno_chat SET estado='pendente', token=?, classificacao=?, relato=?
                    WHERE caso_id=? AND user_id=?""",
                 (token, classification, report, case['caso_id'], user))
    return (f'O relato se refere à recomendação do caso #{case["caso_id"]}?\n'
            f'Recomendação: {case["descricao"]}\nCritério: {case["criterio_sucesso"]}\n'
            f'Relato: {report}\n'
            f'Para confirmar o vínculo e a classificação, digite /confirmar-resultado {token} {classification}. '
            'Você pode trocar a classificação por SUCESSO, PARCIAL, FALHA ou INCONCLUSIVO. '
            'Confirme SUCESSO somente se o critério foi atingido.')


def _review(conn, oq, user, command, argument):
    token, _, classification = argument.partition(' ')
    record = _find(conn, user, token)
    if record is None:
        return 'Esse código de acompanhamento não está disponível na sua conta.'
    case_id = record['caso_id']
    case = _case(conn, user, case_id)
    if command == '/confirmar-resultado':
        if record['estado'] != 'pendente':
            return 'Este resultado já foi processado. Use /retomar-caso para consultar.'
        classification = (classification.strip() or record['classificacao']).upper()
        if classification not in oq.ciclo_adaptativo.RESULTADOS:
            return 'Escolha SUCESSO, PARCIAL, FALHA ou INCONCLUSIVO.'
        if not case or case['action_status'] != 'PENDENTE' or case['case_status'] in ('RESOLVIDO', 'ARQUIVADO'):
            return 'A recomendação mudou ou o caso foi encerrado. O relato não foi aplicado.'
        oq.avaliar_resultado_caso(
            case_id, record['relato'], classification, criterio_atendido=classification == 'SUCESSO',
            justificativa='Classificação e vínculo confirmados pela pessoa no chat.',
            acao_id=record['acao_id'], connection=conn,
        )
        proposal = ADJUSTMENTS.get(classification)
        conn.execute("""UPDATE caso_retorno_chat SET estado='avaliado', classificacao=?, proposta=?
                        WHERE caso_id=? AND user_id=?""", (classification, proposal, case_id, user))
        if proposal:
            return (f'Resultado do caso #{case_id} registrado como {classification}.\n'
                    f'Ajuste proposto: {proposal}\nPara aprovar a próxima ação do caso, use /aprovar-ajuste {token}.')
        return f'Resultado do caso #{case_id} registrado como SUCESSO. O critério foi confirmado e o caso foi resolvido.'

    if command == '/aprovar-ajuste':
        if record['estado'] != 'avaliado' or not record['proposta'] or not case or case['case_status'] in ('RESOLVIDO','ARQUIVADO'):
            return 'Esse ajuste não está disponível para aprovação.'
        pending = conn.execute("""SELECT 1 FROM caso_proximas_acoes WHERE caso_id=? AND user_id=? AND status='PENDENTE'""",
                               (case_id, user)).fetchone()
        if pending:
            return 'O caso já tem outra ação pendente. O ajuste não foi aplicado.'
        action_id = oq.definir_proxima_acao_caso(case_id, record['proposta'], connection=conn)
        conn.execute("""UPDATE caso_retorno_chat SET estado='aprovado', ajuste_id=?
                        WHERE caso_id=? AND user_id=?""", (action_id, case_id, user))
        return f'Ajuste aprovado e registrado como próxima ação do caso #{case_id}. Para desfazer enquanto estiver pendente, use /desfazer-ajuste {token}.'

    if record['estado'] != 'aprovado':
        return 'Esse ajuste não está disponível para desfazer.'
    changed = conn.execute("""UPDATE caso_proximas_acoes SET status='SUBSTITUIDA', atualizado_em=?
        WHERE id=? AND caso_id=? AND user_id=? AND status='PENDENTE'""",
        (oq.motor_resolucao._agora(), record['ajuste_id'], case_id, user))
    if not changed.rowcount:
        return 'A próxima ação já foi alterada ou concluída.'
    oq.registrar_evento_caso(case_id, 'AJUSTE_DESFEITO', record['proposta'], connection=conn)
    conn.execute("""UPDATE caso_retorno_chat SET estado='avaliado', ajuste_id=NULL
                    WHERE caso_id=? AND user_id=?""", (case_id, user))
    return f'Ajuste desfeito no caso #{case_id}. O resultado confirmado continua no histórico.'


def handle_outcome_chat(oq, message):
    command, _, argument = message.strip().partition(' ')
    natural = bool(REPORT.match(message.strip()))
    command = command.casefold()
    argument = argument.strip()
    if command not in COMMANDS and not natural:
        return None
    user = oq.user_id
    with case_connection(oq.motor_casos._conectar) as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute("""CREATE TABLE IF NOT EXISTS caso_retorno_chat (
            caso_id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, acao_id INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'aberto', token TEXT UNIQUE, classificacao TEXT,
            relato TEXT, proposta TEXT, ajuste_id INTEGER
        )""")
        if command == '/experiencias':
            from app.services.confirmed_experience import summary
            scores = summary(oq, connection=conn)
            if not scores:
                return 'Ainda não há cinco casos confirmados para uma mesma estratégia.'
            return 'Resultados confirmados por você (não são validação independente):\n' + '\n'.join(f'{k}: {v["samples"]} casos, {v["success_rate"]:.0%} de sucesso' for k,v in scores.items())
        if command == '/acompanhar':
            return _start(conn, oq, user, argument)
        if command in ('/confirmar-resultado', '/aprovar-ajuste', '/desfazer-ajuste'):
            return _review(conn, oq, user, command, argument)
        if natural:
            ids = conn.execute("""SELECT f.caso_id FROM caso_retorno_chat f JOIN caso_proximas_acoes a
                ON a.id=f.acao_id AND a.user_id=f.user_id AND a.caso_id=f.caso_id
                JOIN casos c ON c.id=f.caso_id AND c.user_id=f.user_id
                WHERE f.user_id=? AND f.estado IN ('aberto','pendente') AND a.status='PENDENTE'
                AND c.status NOT IN ('RESOLVIDO','ARQUIVADO') ORDER BY f.caso_id DESC LIMIT 6""", (user,)).fetchall()
            if not ids:
                return None
            if len(ids) != 1:
                numbers = ', '.join(f'#{row[0]}' for row in ids)
                return f'Há mais de um caso pendente ({numbers}). Use /resultado número CLASSIFICAÇÃO relato para indicar o caso.'
            return _stage(conn, user, _case(conn, user, ids[0][0]), 'INCONCLUSIVO', message.strip())
        raw_id, _, rest = argument.partition(' ')
        raw_id = raw_id.removeprefix('#')
        if not re.fullmatch(r'[0-9]{1,18}', raw_id):
            return 'Informe o número do caso. Use /retomar-caso número ou /resultado número CLASSIFICAÇÃO relato.'
        case = _case(conn, user, int(raw_id))
        if command == '/retomar-caso':
            if not case:
                return 'Não encontrei esse caso de acompanhamento na sua conta.'
            answer = (f'Caso #{case["caso_id"]}: {case["descricao"]}\nCritério: {case["criterio_sucesso"]}\n'
                      f'Estado: {case["case_status"]}.')
            if case['relato']:
                confirmed = case['estado'] != 'pendente'
                answer += f'\nResultado {"confirmado" if confirmed else "a confirmar"}: {case["relato"]}'
            if case['proposta']:
                answer += f'\nAjuste {"aprovado" if case["estado"] == "aprovado" else "proposto"}: {case["proposta"]}'
            if case['estado'] == 'pendente':
                answer += f'\nPara confirmar: /confirmar-resultado {case["token"]} {case["classificacao"]}'
            elif case['proposta']:
                action = '/desfazer-ajuste' if case['estado'] == 'aprovado' else '/aprovar-ajuste'
                answer += f'\n{action} {case["token"]}'
            return answer
        classification, _, report = rest.strip().partition(' ')
        classification, report = classification.upper(), report.strip()
        if classification not in oq.ciclo_adaptativo.RESULTADOS or not report:
            return 'Use /resultado número CLASSIFICAÇÃO e descreva o que aconteceu. Classificações: SUCESSO, PARCIAL, FALHA, INCONCLUSIVO.'
        return _stage(conn, user, case, classification, report)
