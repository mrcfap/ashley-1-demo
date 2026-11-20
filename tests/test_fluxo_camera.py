import base64
import importlib
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.vision.camera import CameraAshley
from app.vision.estado_visual_sessao import EstadoVisualSessao

ROOT = Path(__file__).resolve().parents[1]


def imagem_web(bytes_imagem, mime="image/png"):
    return f"data:{mime};base64," + base64.b64encode(bytes_imagem).decode("ascii")


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    api = importlib.import_module("app.API.app")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ASHLEY_COMMERCIAL_MODE", raising=False)
    monkeypatch.setattr(api.ashley_auth, "DB", tmp_path / "contas.db")
    monkeypatch.setattr(api, "camera_ashley", CameraAshley(tmp_path / "quadros"))
    monkeypatch.setattr(api, "estado_visual_sessao", EstadoVisualSessao())
    monkeypatch.setattr(api.reconhecimento_facial, "pasta_perfis", tmp_path / "perfis")
    monkeypatch.setattr(api, "DB", tmp_path / "ashley.db")
    auth = api.ashley_auth
    senha = "senha-unica-de-teste"
    uid = auth.create("titular@example.test", senha, "Titular de Teste", "1980-01-01")
    segundo = auth.register_user("outro@example.test", senha, "Outra Conta", "1982-01-01")["user_id"]
    a = {"Authorization": "Bearer " + auth.login("titular@example.test", senha)["access_token"]}
    b = {"Authorization": "Bearer " + auth.login("outro@example.test", senha)["access_token"]}
    cliente = TestClient(api.app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 5000))
    foto = (ROOT / "frontend/static/ashley_nova.png").read_bytes()
    return api, cliente, uid, segundo, a, b, foto


def test_descricao_usa_bytes_da_camera_com_consentimento(ambiente, monkeypatch):
    api, cliente, uid, _, auth, _, foto = ambiente
    chamadas = []

    def analisar(caminho, pergunta):
        chamadas.append((Path(caminho).suffix, Path(caminho).read_bytes(), pergunta))
        return {"sucesso": True, "descricao": "Descrição do quadro", "modelo": "simulado"}

    monkeypatch.setattr(api.analisador_visao, "analisar", analisar)
    entrada = {"user_id": uid, "image": imagem_web(foto), "pergunta": "descreva a imagem"}
    sem_consentimento = cliente.post("/vision/capture", headers=auth, json=entrada).json()
    assert sem_consentimento["analise_visual"]["status"] == "aguardando_consentimento_para_analise_multimodal"
    assert chamadas == []
    retorno = cliente.post("/vision/capture", headers=auth, json={
        **entrada, "consentimento_analise_multimodal": True,
    })
    assert retorno.status_code == 200, retorno.text
    assert retorno.json()["analise_visual"]["descricao"] == "Descrição do quadro"
    assert chamadas[0][0:2] == (".png", foto)
    assert "descreva a imagem" in chamadas[0][2]
    assert list(api.camera_ashley.diretorio.iterdir()) == []


def test_chat_sem_quadro_nao_inventa_descricao(ambiente):
    _, cliente, uid, _, auth, _, _ = ambiente
    retorno = cliente.post("/chat", headers=auth, json={
        "user_id": uid, "message": "Ashley, descreva a imagem", "language": "pt-BR",
    })
    assert retorno.status_code == 200, retorno.text
    assert retorno.json()["model"] == "visao-sem-quadro"


def test_exposicao_e_falha_do_provedor_tem_estado_explicito(ambiente, monkeypatch):
    api, cliente, uid, _, auth, _, foto = ambiente
    chamadas = []

    def indisponivel(*args, **kwargs):
        chamadas.append(True)
        raise RuntimeError("simulação de falha")

    monkeypatch.setattr(api.analisador_visao, "analisar", indisponivel)
    _, jpeg_escuro = cv2.imencode(".jpg", np.zeros((240, 320, 3), dtype=np.uint8))
    entrada = {"user_id": uid, "consentimento_analise_multimodal": True}
    escuro = cliente.post("/vision/capture", headers=auth, json={
        **entrada, "image": imagem_web(jpeg_escuro.tobytes(), "image/jpeg"),
    }).json()
    assert escuro["analise_visual"]["status"] == "quadro_escuro"
    assert chamadas == []
    falha = cliente.post("/vision/capture", headers=auth, json={**entrada, "image": imagem_web(foto)}).json()
    assert falha["analise_visual"]["status"] == "analise_multimodal_indisponivel"
    assert chamadas == [True]
    assert list(api.camera_ashley.diretorio.iterdir()) == []


def test_vinculo_legado_e_comparacao_limitados_a_conta(ambiente):
    api, cliente, uid, segundo, auth, outro, foto = ambiente
    engine = api.reconhecimento_facial
    engine.pasta_perfis.mkdir()
    amostra = ROOT / "frontend/static/ashley_nova.png"
    assert engine.cadastrar_pessoa("Titular", [str(amostra)])["sucesso"]
    entrada = {"user_id": uid, "image": imagem_web(foto), "origem": "legado"}
    negado = cliente.post("/vision/profile", headers=auth, json=entrada)
    assert negado.status_code == 422
    confirmar = {"consentimento_cadastro_facial": True}
    negado = cliente.post("/vision/profile", headers=outro, json={**entrada, **confirmar})
    assert negado.status_code == 403
    negado = cliente.post("/vision/profile", headers=outro, json={**entrada, **confirmar, "user_id": segundo})
    assert negado.status_code == 403
    assert cliente.post("/vision/profile", headers=auth, json={**entrada, **confirmar}).json()["status"] == "perfil_vinculado"
    captura = {"user_id": uid, "image": imagem_web(foto)}
    assert cliente.post("/vision/capture", headers=auth, json=captura).json()["identidade_visual"]["identidade"] is None
    captura["consentimento_comparacao_facial"] = True
    match = cliente.post("/vision/capture", headers=auth, json=captura).json()
    assert match["identidade_visual"]["identidade"] == "Titular de Teste"
    visitante = (ROOT / "frontend/static/ashen.png").read_bytes()
    diferente = cliente.post("/vision/capture", headers=auth, json={
        **captura, "image": imagem_web(visitante),
    }).json()["identidade_visual"]
    assert diferente["identidade"] is None
    sem_perfil = cliente.post("/vision/capture", headers=outro, json={**captura, "user_id": segundo}).json()
    assert sem_perfil["identidade_visual"]["status"] == "perfil_facial_ausente"
    assert cliente.get(f"/vision/session/{segundo}", headers=auth).status_code == 403
    assert cliente.delete("/vision/profile", headers=auth).json()["sucesso"]
    assert not engine._arquivo_conta(uid).exists()
    assert (engine.pasta_perfis / "titular.npz").is_file()
    assert list(api.camera_ashley.diretorio.iterdir()) == []


def test_falhas_do_provedor_registradas_com_alternativa_local(ambiente, monkeypatch):
    api, cliente, uid, _, auth, _, foto = ambiente
    chamadas = []

    def nuvem(caminho, pergunta):
        assert Path(caminho).read_bytes() == foto
        assert "descreva a imagem" in pergunta
        chamadas.append("nuvem")
        return {"sucesso": False, "status": "tempo_esgotado"}

    def local(quadro, pergunta, instrucoes):
        assert quadro == foto
        assert "descreva a imagem" in pergunta
        assert "Descreva apenas detalhes visíveis" in instrucoes
        chamadas.append("local")
        return {"sucesso": True, "descricao": "Descrição local", "modelo": "modelo-visual-teste"}

    monkeypatch.setattr(api.analisador_visao, "analisar", nuvem)
    monkeypatch.setattr(api, "descrever_imagem_local", local)
    entrada = {"user_id": uid, "image": imagem_web(foto), "analise_local": True,
               "pergunta": "descreva a imagem"}

    somente_local = cliente.post("/vision/capture", headers=auth, json=entrada).json()["analise_visual"]
    assert chamadas == ["local"]
    assert somente_local["rota"] == "local" and somente_local["falhas"] == []

    chamadas.clear()
    ambas = cliente.post("/vision/capture", headers=auth, json={
        **entrada, "consentimento_analise_multimodal": True,
    }).json()["analise_visual"]
    assert chamadas == ["nuvem", "local"]
    assert ambas["rota"] == "local" and ambas["descricao"] == "Descrição local"
    assert ambas["falhas"] == [{"rota": "nuvem", "status": "tempo_esgotado"}]

    monkeypatch.setattr(api, "descrever_imagem_local",
                        lambda *_: {"sucesso": False, "status": "modelo_local_ausente"})
    sem_descricao = cliente.post("/vision/capture", headers=auth, json={
        **entrada, "consentimento_analise_multimodal": True,
    }).json()["analise_visual"]
    assert not sem_descricao["sucesso"]
    assert sem_descricao["falhas"] == [
        {"rota": "nuvem", "status": "tempo_esgotado"},
        {"rota": "local", "status": "modelo_local_ausente"},
    ]
    assert list(api.camera_ashley.diretorio.iterdir()) == []


def test_ollama_recebe_imagem_apenas_em_modelo_visual_instalado(monkeypatch):
    import json
    import httpx
    from app.services import ollama_local

    http_client = httpx.Client
    chamadas = []
    metadados = {"capabilities": ["completion", "vision"]}
    imagem = b"quadro simulado"

    def receber(request):
        assert request.url.host == "127.0.0.1"
        chamadas.append(request.url.path)
        corpo = json.loads(request.content)
        assert corpo["model"] == "qwen3-vl:2b"
        if request.url.path == "/api/show":
            assert "messages" not in corpo
            return httpx.Response(200, json=metadados)
        assert request.url.path == "/api/chat"
        assert base64.b64decode(corpo["messages"][1]["images"][0], validate=True) == imagem
        assert corpo["messages"][1]["content"] == "Pergunta do usuário"
        return httpx.Response(200, json={"message": {"content": "Descrição local"}})

    def cliente(**kwargs):
        assert kwargs == {"trust_env": False, "follow_redirects": False}
        return http_client(transport=httpx.MockTransport(receber), **kwargs)

    monkeypatch.setattr(ollama_local.httpx, "Client", cliente)
    monkeypatch.setenv("ASHLEY_OLLAMA_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("ASHLEY_OLLAMA_VISION_MODEL", "qwen3-vl:2b")
    dados = ollama_local.descrever_imagem_local(imagem, "Pergunta do usuário", "Instruções")
    assert dados["descricao"] == "Descrição local"
    assert chamadas == ["/api/show", "/api/chat"]

    chamadas.clear()
    metadados["remote_host"] = "https://ollama.com"
    dados = ollama_local.descrever_imagem_local(imagem, "Pergunta do usuário", "Instruções")
    assert dados["status"] == "modelo_local_inadequado"
    assert chamadas == ["/api/show"]


def test_visao_nuvem_classifica_504_e_503_sem_conteudo_bruto(tmp_path, monkeypatch):
    from app.vision.analisador_multimodal import AnalisadorMultimodalAshley

    class ErroProvedor(Exception):
        def __init__(self, code):
            self.code = code
            super().__init__("informação interna de teste")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_VISION_MODELS", raising=False)
    engine = AnalisadorMultimodalAshley()
    engine.cliente = object()
    assert engine.modelo_principal == "gemini-3.5-flash-lite"
    quadro = tmp_path / "teste.jpg"
    quadro.write_bytes(b"captura simulada")
    falhas = iter((504, 503))

    def analisar_modelo(**kwargs):
        raise ErroProvedor(next(falhas))

    monkeypatch.setattr(engine, "_analisar_com_modelo", analisar_modelo)
    resultado = engine.analisar(str(quadro))
    assert resultado["status"] == "servico_sobrecarregado"
    assert [erro["status"] for erro in resultado["erros"]] == ["tempo_esgotado", "servico_sobrecarregado"]
    assert "informação interna" not in str(resultado)
