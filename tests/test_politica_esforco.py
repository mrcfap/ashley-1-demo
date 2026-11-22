import pytest
from app.adaptive_director.politica_esforco import planejar_esforco

def test_niveis_crescentes():
    assert [planejar_esforco(n).max_etapas for n in ("baixo", "medio", "alto", "maximo")] == [2,5,10,20]

def test_exige_aprovacao_externa():
    assert all(planejar_esforco(n).exige_aprovacao_externa for n in ("baixo", "medio", "alto", "maximo"))

def test_rejeita_nivel_invalido():
    with pytest.raises(ValueError):
        planejar_esforco("ilimitado")
