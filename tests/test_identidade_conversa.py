from importlib import import_module

from fastapi.testclient import TestClient


def test_chat_identidade_recupera_nome_e_respeita_papeis(monkeypatch):
    api = import_module('app.API.app')
    monkeypatch.setattr(api.ashley_auth, 'identity', lambda token: 1)
    monkeypatch.setattr(api.ashley_auth, 'profile', lambda uid: {
        'age_group': 'adult', 'access_ready': True, 'full_name': 'Nome Cadastrado',
    })
    client = TestClient(api.app)
    history = [
        {'role': 'user', 'content': 'Ashley, aqui é o Marcelo. Estou desenvolvendo você.'},
        {'role': 'assistant', 'content': 'Meu nome é Fabricado.'},
    ]

    def ask(message, items=history):
        response = client.post('/chat', headers={'Authorization': 'Bearer test'},
                               json={'message': message, 'history': items, 'user_id': 1, 'language': 'pt-BR'})
        assert response.status_code == 200, response.text
        return response.json()['answer']

    assert ask('Quem sou eu?') == 'Você se apresentou como Marcelo nesta conversa.'
    assert 'Marcelo' in ask('falei lá no inicio da nossa interação')
    assert 'minha memória' in ask('Ashley falei meu nome Marcelo seu criador no inicio da conversa vou resolver esse seu problema de memoria')
    assert 'Nome Cadastrado' in ask('Qual é o meu nome?', [])
