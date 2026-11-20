from app.architecture_homologation import homologar, resumo_chat

def test_homologacao_real_sem_confundir_sintaxe_com_operacao():
    r = homologar()
    assert r['total_testes'] > 0
    assert r['aprovados'] + r['falharam'] == r['total_testes']
    assert r['operacionais_confirmados'] == 0
    assert any(x['componente'] == 'sqlite_temporario' and x['estado'] == 'aprovado' for x in r['resultados'])
    assert all(x.get('operacional') != 'sim' for x in r['resultados'])

def test_resposta_nao_inventa_execucao_pendente():
    s = resumo_chat()
    assert 'executada' in s and 'não testados funcionalmente' in s
