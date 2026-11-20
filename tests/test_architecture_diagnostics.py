from app.architecture_diagnostics import COMPONENTES, diagnostico, inspecionar

def test_catalogo_4_20():
    assert len(COMPONENTES["agentes"]) == 4
    assert len(COMPONENTES["motores"]) == 20

def test_diagnostico_nao_afirma_operacional():
    resultado = diagnostico()
    assert resultado["modo"] == "somente_leitura"
    for itens in resultado["grupos"].values():
        for item in itens:
            assert item["operacional"] == "não verificado"
            assert item["carregado"] == "não verificado"

def test_arquivo_ausente():
    assert inspecionar("teste", "app/nao_existe_abc123.py")["estado"] == "ausente"
