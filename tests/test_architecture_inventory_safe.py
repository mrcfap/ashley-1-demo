from app.architecture_diagnostics import ROOT, diagnostico, resposta_para_chat


def test_root_points_to_project():
    assert (ROOT / 'app' / 'API' / 'app.py').is_file()


def test_inventory_scans_real_components():
    data = diagnostico()
    assert data['resumo']['arquivos_python'] >= 150
    assert data['resumo']['falhas_estaticas'] == 0
    assert data['resumo']['operacionais_confirmados'] == 0
    assert any(x['nome'] == 'Planejador' and x['estado'] == 'encontrado' for x in data['referencias']['agentes'])
    assert len(data['versoes']) == 100


def test_chat_uses_actual_inventory():
    answer = resposta_para_chat()
    assert 'Planejador: encontrado' in answer
    assert 'operação não verificada' in answer
