from app.vision.identificacao_multiplos import selecionar_identidade


def test_identifica_cadastrado_com_consentimento():
    assert selecionar_identidade([{"user_id": 3, "nome": "Ana", "similaridade": .82,
                                  "consentimento": True}])["identidade"] == "Ana"


def test_nao_expoe_sem_consentimento():
    assert selecionar_identidade([{"user_id": 3, "nome": "Ana", "similaridade": .99,
                                  "consentimento": False}])["identidade"] is None


def test_empate_nao_adivinha():
    r = selecionar_identidade([{"user_id": 1, "nome": "A", "similaridade": .81, "consentimento": True},
                              {"user_id": 2, "nome": "B", "similaridade": .79, "consentimento": True}])
    assert r["classificacao"] == "incerto"


def test_sem_rosto_cadastrado():
    assert selecionar_identidade([])["classificacao"] == "desconhecido"
