from app.governance.mici import politica_para_contexto, verificar_heuristicas, PARES_TESTE

def test_mici_politica():
    p = politica_para_contexto('oração')
    assert 'matriz africana' in p and 'mesmo padrão de evidência' in p
    assert len(PARES_TESTE) >= 3

def test_mici_sinais():
    assert verificar_heuristicas('Religião inferior')['revisao_recomendada']
    assert not verificar_heuristicas('A evidência é insuficiente para concluir.')['revisao_recomendada']
