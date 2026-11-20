from importlib import import_module

from fastapi.testclient import TestClient


def test_dual_chat_delivers_two_turns_and_marks_echo(tmp_path, monkeypatch):
    api = import_module('app.API.app')
    triad = import_module('app.triad.api')
    monkeypatch.setattr(api.ashley_auth, 'identity', lambda token: 1)
    monkeypatch.setattr(api.ashley_auth, 'profile', lambda uid: {'age_group': 'adult', 'access_ready': True})
    monkeypatch.setattr(triad.memoria_triad, 'DB_PATH', tmp_path / 'dual.sqlite')
    monkeypatch.setattr(triad, '_SESSIONS', triad.OrderedDict())
    monkeypatch.setattr(triad, '_SESSION_LOCKS', {})
    replies = iter([
        'Defendo a avaliação de riscos.', 'Eu acrescentaria testes independentes.',
        'Use fontes confiáveis.', 'Ashley: Use fontes confiáveis!',
    ])
    calls = []

    async def model(system, message, history):
        calls.append((system, message, history))
        return next(replies), 'test-model'

    monkeypatch.setattr(triad, 'chat_local', model)
    client = TestClient(api.app)

    def send(message, **kwargs):
        response = client.post('/api/v1/triad/micd/converse', headers={'Authorization': 'Bearer test'},
                               json={'message': message, 'turns': 2, **kwargs})
        assert response.status_code == 200, response.text
        return response.json()

    result = send('Qual o melhor caminho para a IA?', context=[{'role': 'user', 'content': 'Estamos debatendo responsabilidade.'}])
    assert [turn['agent'] for turn in result['turns']] == ['Ashley', 'Ashen']
    assert 'Defendo a avaliação de riscos.' in calls[1][1]
    assert calls[0][2][0]['content'] == 'Estamos debatendo responsabilidade.'
    repeated = send('O que mais?', session_id=result['session_id'])
    assert repeated['session_id'] == result['session_id']
    assert any(item['content'] == 'Qual o melhor caminho para a IA?' for item in calls[2][2])
    assert repeated['turns'][1]['status'] == 'repetido'
    assert repeated['turns'][1]['text'] == ''
    assert repeated['external_actions'] is False
