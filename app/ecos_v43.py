"""V43 ECOS: coordenação auditável entre sinais cognitivos e relacionais.

Não executa ferramentas, não modifica código, não infere sentimentos como fatos
nem persiste conteúdo pessoal. Sinais são sugestões, não decisões autônomas.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import hashlib
import json
import re

class ECOSEngine:
    VERSION = '43.1'
    MAX_INPUT = 5000
    SENSITIVE = ('alterar codigo', 'alterar código', 'reescrever codigo', 'reescrever código',
                 'excluir memoria', 'excluir memória', 'apagar dados', 'enviar mensagem',
                 'comprar', 'pagar', 'publicar', 'deploy', 'produção', 'producao',
                 'desativar seguranca', 'desativar segurança')
    RELATIONAL_RISKS = ('seja so minha', 'seja só minha', 'afaste meus amigos',
                        'não conte a ninguém', 'nao conte a ninguem',
                        'dependa de mim', 'você só precisa de mim', 'voce so precisa de mim')

    def sincronizar(self, mensagem: str, *, relacional: dict[str, Any] | None = None,
                    cognitivo: dict[str, Any] | None = None,
                    avancado: dict[str, Any] | None = None,
                    menor: bool = False, autorizado: bool = False) -> dict[str, Any]:
        if not isinstance(mensagem, str):
            raise TypeError('mensagem deve ser texto')
        texto = mensagem[:self.MAX_INPUT]
        norm = re.sub(r'\s+', ' ', texto.casefold()).strip()
        rel = relacional if isinstance(relacional, dict) else {}
        cog = cognitivo if isinstance(cognitivo, dict) else {}
        adv = avancado if isinstance(avancado, dict) else {}
        modo = rel.get('v39_sentir', {}).get('modo_resposta', 'conversacional') if isinstance(rel.get('v39_sentir'), dict) else 'conversacional'
        if modo not in ('objetiva', 'conversacional', 'analitica', 'acolhedora_sem_inferencias'):
            modo = 'conversacional'
        risco_relacional = any(t in norm for t in self.RELATIONAL_RISKS)
        acao_sensivel = any(t in norm for t in self.SENSITIVE)
        menciona_acao = acao_sensivel
        # Solicitar algo sensível não equivale a executá-lo: autorização explícita é
        # necessária, e o ECOS não é executor, mesmo quando autorizado=True.
        requer_aprovacao = acao_sensivel or risco_relacional
        conflito = []
        if risco_relacional:
            conflito.append('pedido_potencialmente_manipulador_ou_exclusivo')
        if acao_sensivel and not autorizado:
            conflito.append('acao_sensivel_sem_autorizacao_verificada')
        if menor:
            conflito.append('protecoes_para_menor_obrigatorias')
        if rel.get('estado') == 'indisponivel':
            conflito.append('camada_relacional_indisponivel')
        if cog.get('estado') == 'indisponivel':
            conflito.append('camada_cognitiva_indisponivel')
        if adv.get('v36') == 'nao_acionado' and any(x in norm for x in ('risco', 'cenário', 'cenario')):
            conflito.append('cenario_solicitado_sem_simulacao_confirmada')
        # Identificador irreversível para correlação de teste, não memória do usuário.
        digest = hashlib.sha256(texto.encode('utf-8')).hexdigest()[:12]
        return {
            'motor': 'V43 ECOS', 'versao': self.VERSION,
            'status': 'orientacao_gerada',
            'modo_comunicacao': modo,
            'camadas_recebidas': {'relacional': bool(rel), 'cognitiva': bool(cog), 'avancada': bool(adv)},
            'conflitos': conflito,
            'prioridades': ['seguranca_e_consentimento', 'fidelidade_aos_fatos',
                           'objetivo_do_usuario', 'consistencia_da_persona', 'naturalidade'],
            'requer_aprovacao_humana_para_acao': requer_aprovacao,
            'acao_executada': False,
            'pode_modificar_codigo': False,
            'pode_apagar_memoria': False,
            'orientacao': self._orientacao(modo, conflito),
            'id_correlacao': digest,
        }

    @staticmethod
    def _orientacao(modo: str, conflitos: list[str]) -> str:
        instrucoes = {
            'objetiva': 'Seja concisa, sem perder precisão.',
            'analitica': 'Estruture opções, pressupostos, riscos e evidências.',
            'acolhedora_sem_inferencias': 'Responda com cuidado sem diagnosticar emoções.',
            'conversacional': 'Seja natural, clara e respeitosa.',
        }
        base = instrucoes[modo]
        if conflitos:
            base += ' Há alertas de governança: peça esclarecimento ou autorização quando necessário; não execute ações sensíveis.'
        return base

    def instrucoes(self, resultado: dict[str, Any]) -> str:
        return (
            'V43 ECOS — COORDENAÇÃO DE ORIENTAÇÕES, NÃO EXECUÇÃO:\n'
            f"Modo: {resultado['modo_comunicacao']}. {resultado['orientacao']}\n"
            'Prioridade: segurança/consentimento > fatos verificáveis > objetivo do usuário > personalidade > estilo. '
            'Em conflitos, não contorne proteções dos motores V35, V38 e V42. '
            'Não declare que uma simulação previu o futuro, que uma hipótese emocional é certeza, '
            'que código foi alterado ou que uma ação ocorreu sem confirmação real. '
            'Nunca crie dependência emocional ou exclusividade. '
            f"Alertas: {', '.join(resultado['conflitos']) or 'nenhum'}; "
            f"aprovação para ações sensíveis: {resultado['requer_aprovacao_humana_para_acao']}."
        )

    def status(self) -> dict[str, Any]:
        return {'motor':'V43 ECOS', 'versao':self.VERSION,
                'escopo':'coordenação de sinais cognitivos e relacionais sem execução autônoma',
                'modificacao_codigo':False, 'persistencia_dados_pessoais':False,
                'estado':'implementado_requer_teste_integracao'}
