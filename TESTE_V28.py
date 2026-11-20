from app.future_engines.motores import V28Musica
from app.music.producao import ProducaoMusicalV28, ErroProducaoMusical
v = V28Musica()
assert callable(v.gerar_musica_completa)
assert v.projeto('Teste')['audio_gerado'] is False
try:
    ProducaoMusicalV28(endpoint='', api_key='').gerar(titulo='Teste', letra='letra')
except ErroProducaoMusical:
    pass
else:
    raise AssertionError('Deveria exigir configuração do provedor')
print('OK: V28 importável, gerador conectado e ausência de provedor tratada.')
print('PENDENTE: teste real com provedor de geração musical e integração à interface.')
