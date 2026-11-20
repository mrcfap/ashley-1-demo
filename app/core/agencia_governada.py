"""Executor opt-in V22/V68/V74. Sem shell, sem ferramentas descobertas automaticamente.
O plano de IA é dado não confiável; somente ferramentas registradas podem executar.
"""
from __future__ import annotations
import asyncio
import json
from typing import Any, Callable
from app.integrations.mcp_governance.policy import PolicyRouter

class ExecucaoBloqueada(Exception):
    pass

class AgenciaGovernada:
    def __init__(self, fila, planejador, ferramentas: dict[str, Callable], *, limite_passos=5):
        self.fila = fila
        self.planejador = planejador
        self.ferramentas = dict(ferramentas)
        self.politica = PolicyRouter({name: 'read' for name in self.ferramentas})
        self.limite_passos = max(1, min(int(limite_passos), 10))

    async def executar_proxima(self):
        tarefa = self.fila.proxima()
        if tarefa is None:
            return None
        tid = tarefa['id']
        historico = []
        try:
            for passo in range(self.limite_passos):
                plano = await self.planejador(tarefa['objetivo'], list(historico))
                if not isinstance(plano, dict):
                    raise ExecucaoBloqueada('Plano inválido')
                if plano.get('concluido') is True:
                    resultado = {'resposta': str(plano.get('resposta', ''))[:4000], 'passos': passo}
                    self.fila.concluir(tid, resultado)
                    return resultado
                nome = plano.get('ferramenta')
                args = plano.get('argumentos', {})
                decisao = self.politica.evaluate(tool_name=nome, arguments=args,
                                                  authenticated_user=str(tarefa['user_id']))
                if decisao.status != 'PERMITIDO_PARA_DESPACHO' or nome not in self.ferramentas:
                    raise ExecucaoBloqueada('Ferramenta não autorizada: ' + decisao.reason_code)
                # Limite explícito: não habilitar ferramentas de escrita por este executor.
                resultado = self.ferramentas[nome](**args)
                if asyncio.iscoroutine(resultado):
                    resultado = await asyncio.wait_for(resultado, timeout=15)
                observacao = json.dumps(resultado, ensure_ascii=False, default=str)[:4000]
                historico.append({'ferramenta': nome, 'observacao': observacao})
                self.fila.progresso(tid, min(95, (passo + 1) * 90 // self.limite_passos), 'Observação validada')
            raise ExecucaoBloqueada('Limite de passos atingido')
        except Exception as exc:
            self.fila.falhar(tid, str(exc))
            raise
