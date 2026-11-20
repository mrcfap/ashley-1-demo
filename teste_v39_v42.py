from app.relational_v39_v42 import RelationalV39V42
from app.core.capacidades import CAPACIDADES
m=RelationalV39V42()
a=m.analisar("Estou triste, voltando ao assunto da entrevista.", [{"role":"user","content":"Entrevista na terça"}])
assert "tristeza_declarada" in a["v39_sentir"]["sinais_declarados"]
assert a["v41_continuum"]["retomada_solicitada"]
assert not a["v42_horizonte"]["pode_agir_sem_autorizacao"]
assert all("v"+str(i) in " ".join(CAPACIDADES) for i in range(39,43))
assert "Não invente lembranças" in m.instrucoes(a)
print("V39-V42: testes locais aprovados")
