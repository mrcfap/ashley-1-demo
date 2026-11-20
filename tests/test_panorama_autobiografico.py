from app.memory.memoria_longa import MemoriaLongoPrazo
from app.memory.rastreabilidade_cognitiva import (
    consulta_autobiografica, consulta_catalogo, contexto_rastreavel,
)


def test_panorama_diversificado(tmp_path):
    memoria = MemoriaLongoPrazo(tmp_path / "mem.db")
    for n in range(30):
        memoria.guardar(1, "projeto", f"motor_{n}", f"Motor cognitivo {n}")
    memoria.guardar(1, "profissao", "ocupacao", "Educador social")
    memoria.guardar(1, "literatura", "pseudonimo", "Richards Marcells")
    memoria.guardar(1, "interesses", "musica", "Rock")
    memoria.guardar(2, "profissao", "ocupacao", "Outro usuario")
    texto = contexto_rastreavel(memoria, 1, "Fale mais de mim sobre as informações que te passei em conversas anteriores")
    assert "Educador social" in texto
    assert "Richards Marcells" in texto
    assert "Rock" in texto
    assert "Outro usuario" not in texto


def test_catalogo_sem_titulos_inventados(tmp_path):
    memoria = MemoriaLongoPrazo(tmp_path / "mem.db")
    memoria.guardar(1, "livros", "pacto do lobo", "Pacto do Lobo")
    memoria.guardar(1, "livros", "orbita", "Órbita")
    texto = contexto_rastreavel(memoria, 1, "Fale das minhas obras os nomes delas")
    assert "Pacto do Lobo" in texto
    assert "Órbita" in texto
    assert "Alice" not in texto
    assert consulta_catalogo("Fale das minhas obras os nomes delas")
    assert consulta_autobiografica("Fale mais de mim sobre as informações que te passei em conversas anteriores")
