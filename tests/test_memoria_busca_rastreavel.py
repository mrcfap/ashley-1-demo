import sqlite3

from app.memory.memoria_longa import MemoriaLongoPrazo
from app.memory.rastreabilidade_cognitiva import contexto_rastreavel


def test_busca_antiga_e_alias(tmp_path):
    memoria = MemoriaLongoPrazo(tmp_path / "memory.db")
    memoria.guardar(1, "pessoal", "animal de estimacao", "Meu cachorro se chama Pitu")
    for i in range(230):
        memoria.guardar(1, "outros", f"nota_{i}", f"Registro sem relacao {i}", importancia=0.99)
    resultados = memoria.buscar(1, "Qual o nome do meu cachorro?")
    assert resultados
    assert resultados[0]["conteudo"] == "Meu cachorro se chama Pitu"
    assert "Pitu" in contexto_rastreavel(memoria, 1, "meu pet")
    assert memoria.buscar(1, "termoabsolutamenteinexistente") == []


def test_isolamento_e_temporalidade(tmp_path):
    memoria = MemoriaLongoPrazo(tmp_path / "memory.db")
    memoria.guardar(1, "identidade", "autor", "Richards Marcells")
    memoria.guardar(2, "identidade", "autor", "Outro autor")
    assert all("Outro" not in x["conteudo"] for x in memoria.buscar(1, "autor"))
    primeiro = memoria.buscar(1, "autor")[0]["criado_em"]
    memoria.guardar(1, "identidade", "autor", "Richards Marcells atualizado")
    atual = memoria.buscar(1, "autor")[0]
    assert atual["criado_em"] == primeiro
    assert atual["atualizado_em"]
    assert "criado_em=" in contexto_rastreavel(memoria, 1, "autor")
