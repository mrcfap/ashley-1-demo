import pytest
from app.nextgen.symphony_bridge import SymphonyOrchestratorBridge


class FakeOrchestrator:
    def __init__(self):
        self.calls = []

    def selecionar_motores_cognitivos(self, mensagem, complexidade="baixa"):
        self.calls.append((mensagem, complexidade))
        return {"v12": True, "v18": True}


def test_symphony_seleciona_motores_existentes():
    fake = FakeOrchestrator()
    bridge = SymphonyOrchestratorBridge(fake)

    result = bridge.prepare("Analisar um problema", "alta")

    assert result["selected_engines"]["v18"] is True
    assert fake.calls == [("Analisar um problema", "alta")]


def test_symphony_nao_autoriza_execucao():
    bridge = SymphonyOrchestratorBridge(FakeOrchestrator())

    result = bridge.prepare("Planejar projeto")

    assert result["execution_authorized"] is False
    assert result["external_actions_enabled"] is False


def test_symphony_exige_governanca():
    bridge = SymphonyOrchestratorBridge(FakeOrchestrator())

    result = bridge.prepare("Avaliar uma proposta")

    assert result["requires_trusted_policy_check"] is True
    assert result["requires_human_approval_for_sensitive_actions"] is True


def test_symphony_rejeita_objetivo_vazio():
    bridge = SymphonyOrchestratorBridge(FakeOrchestrator())

    with pytest.raises(ValueError):
        bridge.prepare("   ")


def test_symphony_rejeita_complexidade_invalida():
    bridge = SymphonyOrchestratorBridge(FakeOrchestrator())

    with pytest.raises(ValueError):
        bridge.prepare("Analisar projeto", "extrema")
