from importlib import import_module

from fastapi.testclient import TestClient


def test_lembrete_dupla_e_chat_individual(tmp_path, monkeypatch):
    api = import_module('app.API.app')
    triad = import_module('app.triad.api')
    monkeypatch.setattr(api.ashley_auth, 'identity', lambda token: int(token))
    monkeypatch.setattr(api.ashley_auth, 'profile', lambda uid: {'age_group': 'adult', 'access_ready': True})
    monkeypatch.setattr(triad.memoria_triad, 'DB_PATH', tmp_path / 'lembretes.sqlite')
    monkeypatch.setattr(triad, '_SESSIONS', triad.OrderedDict())
    monkeypatch.setattr(triad, '_SESSION_LOCKS', {})
    client = TestClient(api.app)
    r = client.post('/api/v1/triad/micd/converse', headers={'Authorization': 'Bearer 1'},
                    json={'message': 'palavra chave guarde ela "foco" e o numero 3'})
    assert r.status_code == 200, r.text
    assert 'Guardei' in r.json()['turns'][0]['text']

    def ask(user, persona, msg):
        result = client.post('/chat', headers={'Authorization': f'Bearer {user}'},
                             json={'user_id': user, 'persona': persona, 'language': 'pt-BR', 'message': msg})
        assert result.status_code == 200, result.text
        return result.json()['answer']

    pergunta = 'me diz a palavra chave e o numero que pedi para guardar'
    for persona in ('Ashley', 'Ashen'):
        resposta = ask(1, persona, pergunta)
        assert '“foco”' in resposta and 'número é 3' in resposta
    assert 'Ainda não encontrei' in ask(2, 'Ashen', pergunta)
    assert 'Guardei' in ask(1, 'Ashley', 'Guarde a palavra "disciplina".')
    assert '“disciplina”' in ask(1, 'Ashen', 'qual foi a palavra que pedi para vc guardar')
    assert 'guardar é 3' in ask(1, 'Ashen', 'qual o numero que pedi para guardar')

    assert 'Guardei' in ask(2, 'Ashley', 'faça isto mas antes guarde esta palavra "foco" e agora apresente este detalhe')
    assert ask(2, 'Ashley', 'qual foi a palavra que pedi para vc guardar') == 'A palavra que você pediu para guardar é “foco”.'
    assert 'Ainda não encontrei um número' in ask(2, 'Ashley', pergunta)
