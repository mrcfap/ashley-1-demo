from app.architecture_integration_audit import auditar_integracoes


def test_auditoria_distingue_presenca_de_operacao():
    relatorio = auditar_integracoes()
    assert relatorio["modo"] == "auditoria_estatica_sem_efeitos_colaterais"
    assert relatorio["total"] > 0
    assert relatorio["funcionamento_comprovado"] == 0
    assert all(item["funcionamento_comprovado"] is False for item in relatorio["componentes"])
    assert any("orquestrador" in item["componente"] for item in relatorio["componentes"])


def test_agentes_sem_executar_ferramentas():
    relatorio = auditar_integracoes()
    assert any(item["componente"].startswith("app/agents/") for item in relatorio["componentes"])
    assert all(item["estado"] in {
        "falha_estatica", "instanciacao_referenciada",
        "importacao_referenciada", "sem_ligacao_direta_identificada"
    } for item in relatorio["componentes"])
