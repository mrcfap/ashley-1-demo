from app.nextgen.nextgen_planning import extended_inventory, select_nextgen

def test_inventory_legacy_preserved():
    old={'range':'V1-V84','engines':[{'motor':'V1','status':'historico'}], 'files_parsed_attempted':164,'parse_errors':['example']}
    merged=extended_inventory(old)
    assert merged['range']=='V1-V100'
    assert merged['engines'][0]==old['engines'][0]
    assert len(merged['engines'])==17
    assert [e['motor'] for e in merged['engines'][1:]]==[f'V{i}' for i in range(85,101)]
    assert merged['parse_errors']==['example']
    assert merged['all_engines_operational'] is False

def test_selection_explainable():
    selected=select_nextgen('Quero investigar evidências e proteger privacidade dos dados pessoais')
    assert {'V89','V91'} <= {e['id'] for e in selected}
    assert all(e['executed'] is False and e['planned_only'] for e in selected)

def test_no_match_no_invented_execution():
    assert select_nextgen('Bom dia!') == []

def test_selection_limited():
    assert len(select_nextgen('memória cenário código previsão investigar latência privacidade empatia agentes integrar'))<=5

def test_symphony_bridge_selects_without_execution():
    from app.nextgen.symphony_bridge import SymphonyOrchestratorBridge
    class FakeOrchestrator:
        def selecionar_motores_cognitivos(self, objective, complexidade):
            return {'mode':'fake','complexity':complexidade}
    result=SymphonyOrchestratorBridge(FakeOrchestrator()).prepare('Investigar evidências e proteger privacidade', 'media')
    assert {'V89','V91'} <= {e['id'] for e in result['nextgen_selected_engines']}
    assert result['execution_authorized'] is False
    assert result['external_actions_enabled'] is False
    assert len(result['nextgen_capability_catalog']) == 16
