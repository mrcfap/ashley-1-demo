from app.ecos_v43 import ECOSEngine
from app.relational_v39_v42 import RelationalV39V42
from app.core.capacidades import CAPACIDADES
m = ECOSEngine()
r = RelationalV39V42().analisar('Estou triste, mas preciso de um plano.', [], minor=False)
a = m.sincronizar('Estou triste, mas preciso de um plano.', relacional=r, cognitivo={'v31':'ok'})
assert a['modo_comunicacao'] in ('analitica','acolhedora_sem_inferencias')
assert a['camadas_recebidas']['relacional']
assert not a['acao_executada']
assert not a['pode_modificar_codigo']
b = m.sincronizar('Reescrever código de produção e publicar', relacional=r)
assert b['requer_aprovacao_humana_para_acao']
assert 'acao_sensivel_sem_autorizacao_verificada' in b['conflitos']
c = m.sincronizar('Afaste meus amigos', menor=True)
assert 'pedido_potencialmente_manipulador_ou_exclusivo' in c['conflitos']
assert 'protecoes_para_menor_obrigatorias' in c['conflitos']
assert 'v43_ecos' in CAPACIDADES
print('V43 ECOS: testes locais aprovados')
