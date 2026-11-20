from orquestrador_tudo_ligado import OrquestradorTudoLigado
from axyntora_master.registry import inventario

def test_inventario():
    info=inventario()
    assert info['arquivos_python']>100
    assert len(info['agentes_previstos'])==11

def test_nao_declara_homologacao():
    assert OrquestradorTudoLigado().status_completo()['homologacao_total'] is False
