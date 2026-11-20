"""Ponte conservadora entre motores V48-V61 e a API da Ashley.

Não executa código, não grava dados, não consulta redes nem envia mensagens.
Inventário de importação NÃO equivale a integração funcional completa.
"""
from __future__ import annotations
from importlib import import_module

MODULOS = {
 'V48':'app.future_v48_v51', 'V49':'app.future_v48_v51',
 'V50':'app.future_v48_v51', 'V51':'app.future_v48_v51',
 'V52':'app.synapse_v52.engine',
 'V53':'app.future_v53_v56', 'V54':'app.future_v53_v56',
 'V55':'app.future_v53_v56', 'V56':'app.future_v53_v56',
 'V57':'app.fortress_v57.engine', 'V58':'app.legacy_v58.engine',
 'V59':'app.neuropsyche_v59.engine',
 'V60':'app.veritas_v60.engine', 'V61':'app.praxis_v61.engine',
}
CLASSES = {
 'V48':'LearningV48','V49':'FinOpsV49','V50':'WatchdogV50','V51':'SyncV51',
 'V52':'SynapseV52','V53':'PrometheusV53','V54':'ConductorV54',
 'V55':'GuardianV55','V56':'HorizonV56',
 'V57':'CircuitBreaker','V58':'LegacyTracker',
 'V59':'NeuroPsycheV59','V60':'VeritasV60','V61':'PraxisV61',
}


def inventario_v48_v61():
    motores={}
    for version, module_name in MODULOS.items():
        try:
            module=import_module(module_name)
            cls=getattr(module, CLASSES[version])
            motores[version]={'importavel':True,'classe':cls.__name__,
                              'uso_no_chat':'orientacao_contextual' if version=='V59' else
                              ('politica_em_falha' if version=='V55' else 'nao_integrado_ao_chat')}
        except (ImportError,AttributeError,RuntimeError) as exc:
            motores[version]={'importavel':False,'erro_tipo':type(exc).__name__}
    return {'escopo':'V48-V61','motores':motores,
            'observacao':'Importação não prova execução real nem validação clínica. Integração gradual.'}


def orientacao_v59(texto:str, *, menor:bool=False)->str:
    from app.neuropsyche_v59.engine import NeuroPsycheV59
    # O motor só é invocado para sinais textuais, sem guardar dados sensíveis.
    # Idade 17 é categoria conservadora para menor; não representa idade real.
    resultado=NeuroPsycheV59().assess(texto, age=17 if menor else None,
                                      guardian_approved=False, consent_to_memory=False)
    if resultado['level'] not in ('urgent', 'support', 'restricted'):
        return ''
    return ('V59 NEUROPSYCHE — APOIO EMOCIONAL NÃO CLÍNICO. '
            'Acolha sem diagnosticar nem prometer tratamento. '
            'Não substitua psicólogo ou psiquiatra. Não armazene automaticamente '
            'dados de saúde mental. Se houver risco imediato, priorize segurança '
            'e apoio humano. Orientação de segurança: '+resultado['response'])


def politica_recuperacao_v55(falha:str)->dict:
    from app.future_v53_v56 import GuardianV55
    return GuardianV55().decide(falha, attempts=1, idempotent=False)
