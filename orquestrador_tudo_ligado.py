"""Camada de integração sem simular respostas ou homologações."""
from axyntora_master.registry import inventario
class OrquestradorTudoLigado:
    def status_completo(self):
        info=inventario()
        return {'master':'Axyntora','integracao':'API legada preservada','homologacao_total':False,'todos_homologados':False,'status':'integracao_em_validacao','inventario':info}
    def processar(self, mensagem, **kwargs):
        raise RuntimeError('Use POST /chat na API original com autenticação. Este adaptador não contorna controles de segurança.')
    def processar_camera_stream(self,*args,**kwargs):
        raise RuntimeError('Use os endpoints de câmera existentes, com autenticação e consentimento.')
