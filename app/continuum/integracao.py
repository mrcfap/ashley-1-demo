"""Integração real do PlannerAshley, CriticAshley e MemoriaLongoPrazo.

A evolução é uma seleção de estratégia *pré-aprovada*; não há escrita de código,
execução de ferramentas, navegação web nem alegação de aprendizado de modelo.
"""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
from app.agents.planner import PlannerAshley
from app.agents.critic import CriticAshley
from app.memory.memoria_longa import MemoriaLongoPrazo
from app.continuum.benchmark import executar, registrar, task_id

STRATEGY_KEY = 'normalizar_espacos_v1'


def _estrategia(task, melhorada):
    if task['tipo'] == 'normalizar' and not melhorada:
        return str(task['entrada']).casefold()  # baseline simples, intencionalmente imperfeito
    return executar(task)


def _ler_estrategia(memoria, usuario):
    for item in memoria.buscar(usuario, 'continuum normalizar', limite=30):
        if item.get('categoria') == 'continuum_estrategia' and item.get('chave') == STRATEGY_KEY:
            try:
                return bool(json.loads(item['conteudo'])['habilitada'])
            except (ValueError, KeyError, TypeError):
                return False
    return False


def rodar_ciclo(tarefas_treino, tarefas_ineditas, db_memoria, db_metricas, usuario=1, promover=False):
    """Treino e avaliação inédita são separados; promoção depende de aprovação explícita.

    O benchmark não envia os exemplos inéditos à memória de aprendizagem.
    """
    if not tarefas_treino or not tarefas_ineditas:
        raise ValueError('São necessárias tarefas de treino e inéditas')
    def conteudo_id(t):
        return hashlib.sha256(json.dumps({k:v for k,v in t.items() if k != 'grupo'}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    ids_treino = {conteudo_id(t) for t in tarefas_treino}
    if ids_treino.intersection(conteudo_id(t) for t in tarefas_ineditas):
        raise ValueError('Vazamento: tarefa presente em treino e inédito')
    for grupo, tarefas in [('treino', tarefas_treino), ('inedito', tarefas_ineditas)]:
        for t in tarefas:
            if t.get('grupo') != grupo:
                raise ValueError('Grupo de tarefa inconsistente')
    memoria = MemoriaLongoPrazo(db_memoria)
    planner, critic = PlannerAshley(), CriticAshley()
    estrategia_anterior = _ler_estrategia(memoria, usuario)

    def fase(tarefas, estrategia):
        resultados = []
        for t in tarefas:
            plano = planner.criar_plano(f"Executar tarefa offline {t['tipo']}", experiencias=[], ferramentas_disponiveis=[])
            inicio = time.perf_counter()
            try:
                obtido = _estrategia(t, estrategia)
                erro = None
            except (ValueError, KeyError, TypeError) as exc:
                obtido, erro = None, type(exc).__name__
            avaliacao = critic.validar_resultado(plano['objetivo'], {'sucesso': erro is None, 'dados': obtido, 'erro': erro}, plano)
            correto = erro is None and obtido == t['esperado']
            duracao = round((time.perf_counter()-inicio)*1000, 3)
            registrar(db_metricas, t, obtido, correto, duracao, usuario=usuario)
            resultados.append({'id': task_id(t), 'acerto': correto, 'critico_aprovou': avaliacao['aprovado'],
                               'plano': plano['status'], 'duracao_ms': duracao})
        return {'total': len(resultados), 'acertos': sum(x['acerto'] for x in resultados),
                'taxa': round(sum(x['acerto'] for x in resultados)/len(resultados), 4), 'resultados': resultados}

    treino_antes = fase(tarefas_treino, estrategia_anterior)
    proposta = (not estrategia_anterior and any(t['tipo'] == 'normalizar' for t in tarefas_treino)
                and any(not r['acerto'] for r in treino_antes['resultados']))
    # Somente uma estratégia fixa e revisada; nenhum código é gerado nem promovido.
    treino_proposto = fase(tarefas_treino, True) if proposta else treino_antes
    pode_promover = proposta and treino_proposto['acertos'] > treino_antes['acertos']
    if promover and pode_promover:
        memoria.guardar(usuario, 'continuum_estrategia', STRATEGY_KEY,
                        json.dumps({'habilitada': True, 'origem': 'promocao_explicita',
                                    'acertos_antes': treino_antes['acertos'], 'acertos_depois': treino_proposto['acertos']}))
    estrategia_final = estrategia_anterior or (promover and pode_promover)
    # Avaliação inédita ocorre só depois da decisão de promover; nunca retroalimenta estratégia.
    inedito = fase(tarefas_ineditas, estrategia_final)
    return {'treino_antes': treino_antes, 'treino_proposto': treino_proposto,
            'inedito': inedito, 'proposta_melhoria': proposta,
            'promovida': bool(promover and pode_promover), 'estrategia_ativa': bool(estrategia_final),
            'limites': 'Estratégia determinística pré-aprovada; não é aprendizado autônomo nem avaliação de LLM.'}


def exemplos():
    return ([{'tipo':'normalizar','entrada':'  Bom   DIA ','esperado':'bom dia','grupo':'treino'},
             {'tipo':'somar','entrada':[2,3],'esperado':5,'grupo':'treino'}],
            [{'tipo':'normalizar','entrada':'  Olá   MUNDO ','esperado':'olá mundo','grupo':'inedito'},
             {'tipo':'somar','entrada':[9,1],'esperado':10,'grupo':'inedito'}])


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--memoria', default='data/continuum_memoria.sqlite3')
    p.add_argument('--metricas', default='data/continuum_metricas.sqlite3')
    p.add_argument('--promover', action='store_true', help='Aprovar promoção da estratégia pré-aprovada')
    args = p.parse_args()
    print(json.dumps(rodar_ciclo(*exemplos(), args.memoria, args.metricas, promover=args.promover),
                     ensure_ascii=False, indent=2))
