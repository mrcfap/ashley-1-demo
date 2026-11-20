import sys
import types

def test_visao_nao_interrompe_api_com_sdk_incompleto(monkeypatch):
    from app.vision.analisador_multimodal import AnalisadorMultimodalAshley
    fake_google = types.ModuleType("google")
    fake_genai = types.ModuleType("google.genai")
    fake_types = types.ModuleType("google.genai.types")
    fake_google.genai = fake_genai
    fake_genai.types = fake_types
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    engine = AnalisadorMultimodalAshley()
    assert engine.cliente is None
    assert engine.ativo is False
    assert "Client" in engine.estado()["erro_inicializacao"]
    assert engine.analisar("inexistente.png")["status"] == "dependencia_indisponivel"
