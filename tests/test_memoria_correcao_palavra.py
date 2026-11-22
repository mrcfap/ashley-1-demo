"""Testes isolados de histórico de correções por conta."""
from app.services.memoria_compartilhada import responder_lembrete
from app.triad import persistencia


def test_correcao_historico_e_conta(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, 'DB_PATH', tmp_path / 'memoria.db')
    assert 'Jacke' in responder_lembrete('usuario-1', 'guarde esta palavra "Jacke"')
    assert 'Jack' in responder_lembrete('usuario-1', 'Coloque Jack em vez de Jacke')
    assert 'Jaque' in responder_lembrete('usuario-1', 'Coloque Jaque em vez de Jack')
    resposta = responder_lembrete('usuario-1', 'quais as três correções da palavra que pedi para guardar?')
    assert 'Jacke → Jack → Jaque' in resposta
    assert 'Jaque' in responder_lembrete('usuario-1', 'qual a palavra que pedi para guardar')
    assert 'não encontrei' in responder_lembrete('usuario-2', 'qual a palavra que pedi para guardar').lower()
    assert 'Não alterei' in responder_lembrete('usuario-1', 'Coloque Outra em vez de Jacke')
