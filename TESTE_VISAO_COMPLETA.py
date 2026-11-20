from app.vision.presenca_ao_vivo import PresencaAoVivo,PresencaInput

def test_presenca():
    p=PresencaAoVivo(detector=lambda _:1)
    d=PresencaInput(user_id=1,image='x'*30,camera_autorizada=True,interacao_espontanea=True)
    assert not p.processar(d)['eventos']
    assert any(e['tipo']=='convite_conversa' for e in p.processar(d)['eventos'])
    assert not p.processar(d)['eventos']
    assert p.processar(d.model_copy(update={'camera_autorizada':False}))['camera_ativa'] is False
    assert p.status(1)['ativo'] is False

if __name__=='__main__':
    test_presenca();print('TESTE PRESENÇA: OK')
