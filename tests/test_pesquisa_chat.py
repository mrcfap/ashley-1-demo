from types import SimpleNamespace

import pytest

from app.services.pesquisa_chat import PEDIDO_WEB, pesquisar_no_chat


@pytest.mark.asyncio
async def test_busca_explicitamente_limitada_ao_bcb():
    mensagem = 'Ashley, use a pesquisa web agora. Consulte o site oficial do Banco Central do Brasil e me diga a meta Selic.'
    assert PEDIDO_WEB.search(mensagem)

    async def search(consulta):
        assert consulta.startswith('site:bcb.gov.br ')
        return SimpleNamespace(sucesso=True, dados=[
            {'url': 'https://bcb.gov.br.example.org/pagina', 'conteudo': 'Valor inventado'},
            {'url': 'https://www.bcb.gov.br/controleinflacao/historicotaxasjuros', 'conteudo': 'Em 04/11/2026, 13,75%.'},
        ])

    result = await pesquisar_no_chat(SimpleNamespace(pesquisar_web=search), mensagem)
    assert result['web_results'] == 1
    assert '13,75%' in result['answer']
    assert 'example.org' not in result['answer']


@pytest.mark.asyncio
async def test_busca_sem_retorno_nao_inventa_resposta():
    async def search(consulta):
        return SimpleNamespace(sucesso=False, dados=[])

    result = await pesquisar_no_chat(SimpleNamespace(pesquisar_web=search), 'Pesquise na web agora.')
    assert result['web_used'] and not result['web_success']
    assert result['web_sources'] == []


def test_chat_usa_ferramenta_sem_chamar_modelo(monkeypatch):
    from importlib import import_module
    from fastapi.testclient import TestClient

    api = import_module("app.API.app")
    chamadas = []

    async def search(consulta):
        chamadas.append(consulta)
        return SimpleNamespace(sucesso=False, dados=[])

    monkeypatch.setattr(api.ashley_auth, "identity", lambda _: 1)
    monkeypatch.setattr(api.ashley_auth, "profile", lambda _: {"age_group": "adult", "access_ready": True})
    monkeypatch.setattr(api, "orquestrador", lambda _: SimpleNamespace(ferramentas=SimpleNamespace(pesquisar_web=search)))
    response = TestClient(api.app).post(
        "/chat", headers={"Authorization": "Bearer test"},
        json={"user_id": 1, "language": "pt-BR", "message": "Use a pesquisa web agora. Consulte o Banco Central do Brasil sobre a meta Selic."},
    )
    assert response.status_code == 200
    assert len(chamadas) == 1
    assert response.json()["model"] == "pesquisa-web"
    assert not response.json()["web_success"]
