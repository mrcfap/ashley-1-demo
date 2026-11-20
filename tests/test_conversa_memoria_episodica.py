from importlib import import_module

from fastapi.testclient import TestClient


def setup_api(tmp_path, monkeypatch):
    api = import_module('app.API.app')
    triad = import_module('app.triad.api')
    monkeypatch.setattr(api.ashley_auth, 'identity', lambda token: int(token))
    monkeypatch.setattr(api.ashley_auth, 'profile', lambda uid: {
        'age_group': 'adult', 'access_ready': True,
    })
    monkeypatch.setattr(triad.memoria_triad, 'DB_PATH', tmp_path / 'conversa.db')
    monkeypatch.setattr(triad, '_SESSIONS', triad.OrderedDict())
    monkeypatch.setattr(triad, '_SESSION_LOCKS', {})
    return api, triad


def enviar(client, mensagem, usuario=1, dual=True, **dados):
    if not dual:
        dados.update(user_id=usuario, persona='Ashen', language='pt-BR')
    resposta = client.post('/api/v1/triad/micd/converse' if dual else '/chat',
                          headers={'Authorization': f'Bearer {usuario}'},
                          json={'message': mensagem, **dados})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_dupla_saudacao_e_resposta_direta(tmp_path, monkeypatch):
    api, triad = setup_api(tmp_path, monkeypatch)
    chamados = []
    respostas = iter([
        'A IA poderá acompanhar projetos entre conversas.',
        'Ashley respondeu sobre o futuro da IA. A resposta é relevante e direta.',
        'Eu espero que cada ação autorizada tenha um registro verificável.',
    ])

    async def modelo(system, message, history):
        chamados.append((system, message))
        return next(respostas), 'modelo-teste'

    monkeypatch.setattr(triad, 'chat_local', modelo)
    with TestClient(api.app) as client:
        saudacao = enviar(client, 'boa tarde')
        assert len(saudacao['turns']) == 2
        assert all(t['text'].startswith('Boa tarde!') for t in saudacao['turns'])
        assert not chamados
        resposta = enviar(client, 'fale algo sobre o futuro da IA',
                          session_id=saudacao['session_id'])
        assert 'registro verificável' in resposta['turns'][1]['text']
        assert 'Ashley respondeu' not in resposta['turns'][1]['text']
        assert len(chamados) == 3
        assert 'acompanhar projetos' in chamados[1][1]
        assert 'acompanhar projetos' not in chamados[2][1]


def test_correcao_em_nova_conversa_e_apos_reinicio(tmp_path, monkeypatch):
    api, triad = setup_api(tmp_path, monkeypatch)
    with TestClient(api.app) as client:
        enviar(client, 'Guarde o fato fornecedor: Aurora')
        editar = enviar(client, 'Corrija o fato fornecedor: Horizonte', dual=False)
        assert 'Horizonte' in editar['answer']

    triad._SESSIONS.clear()
    triad._SESSION_LOCKS.clear()
    from app.services.memoria_episodica import consolidar_fatos, contexto_fatos

    consolidar_fatos()
    with TestClient(api.app) as client:
        consulta = enviar(client, 'Qual é o fato fornecedor?')
        assert 'Horizonte' in consulta['turns'][0]['text']
        assert 'Aurora' not in consulta['turns'][0]['text']
        assert 'Ainda não há' in enviar(
            client, 'Qual é o fato fornecedor?', usuario=2, dual=False
        )['answer']
        assert 'Horizonte' in contexto_fatos(1, 'Quando mudar de fornecedor?')
        assert not contexto_fatos(2, 'Quando mudar de fornecedor?')


def test_comite_usa_quatro_perspectivas(tmp_path, monkeypatch):
    api, triad = setup_api(tmp_path, monkeypatch)
    prompts = []
    respostas = iter(['Análise inicial.', 'A restrição é o prazo.',
                     'Uma opção é reduzir o escopo.', 'Comece com um teste de uma semana.'])

    async def modelo(system, message, history):
        prompts.append(message)
        return next(respostas), 'modelo-teste'

    monkeypatch.setattr(triad, 'chat_local', modelo)
    with TestClient(api.app) as client:
        resultado = enviar(client, 'Compare opções para um piloto.', turns=4)
    assert [t['agent'] for t in resultado['turns']] == ['Ashley', 'Ashen', 'Ashley', 'Ashen']
    assert 'perspectiva prática' in prompts[1]
    assert 'alternativa criativa' in prompts[2]
    assert 'Sintetize as contribuições' in prompts[3]
    assert 'teste de uma semana' in resultado['turns'][-1]['text']
