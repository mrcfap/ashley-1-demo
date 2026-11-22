"""Integra PlannerAshley, CriticAshley e MemoriaLongoPrazo no benchmark offline.
Não executa código arbitrário, não altera produção e não treina modelos.
"""
import hashlib
import json
from app.agents.planner import PlannerAshley
from app.agents.critic import CriticAshley
from app.memory.memoria_longa import MemoriaLongoPrazo
from app.continuum.benchmark import executar, registrar

CHAVE = "normalizar_espacos_v1"


def _id(t):
    return hashlib.sha256(json.dumps({k:v for k,v in t.items() if k != "grupo"},sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def ciclo(treino, ineditas, memoria_db, metricas_db, usuario=1, aprovar=False):
    if not treino or not ineditas or {_id(t) for t in treino} & {_id(t) for t in ineditas}:
        raise ValueError("Treino e ineditas devem ser disjuntos e não vazios")
    for grupo, tarefas in (("treino",treino),("inedito",ineditas)):
        if any(t.get("grupo") != grupo for t in tarefas):
            raise ValueError("Grupo inconsistente")
    memoria = MemoriaLongoPrazo(memoria_db)
    registros = memoria.buscar(usuario,"continuum normalizar",limite=30)
    ativa = any(x.get("categoria") == "continuum_estrategia" and x.get("chave") == CHAVE
                and json.loads(x["conteudo"]).get("habilitada") for x in registros)
    planner, critic = PlannerAshley(), CriticAshley()
    def avaliar(tarefas, melhorada):
        respostas=[]
        for t in tarefas:
            plano=planner.criar_plano("Executar tarefa offline "+t["tipo"], ferramentas_disponiveis=[])
            try:
                obtido = (str(t["entrada"]).casefold() if t["tipo"]=="normalizar" and not melhorada
                          else executar(t))
                erro = None
            except (ValueError,KeyError,TypeError) as e:
                obtido,erro=None,type(e).__name__
            revisao=critic.validar_resultado(plano["objetivo"],{"sucesso":erro is None,"dados":obtido,"erro":erro},plano)
            acerto=erro is None and obtido==t["esperado"]
            registrar(metricas_db,t,obtido,acerto,0.0,usuario=usuario)
            respostas.append({"acerto":acerto,"critic_aprovou":revisao["aprovado"],"plano":plano["status"]})
        return {"total":len(respostas),"acertos":sum(x["acerto"] for x in respostas),
                "taxa":round(sum(x["acerto"] for x in respostas)/len(respostas),4),"resultados":respostas}
    antes=avaliar(treino,ativa)
    proposta=(not ativa and any(t["tipo"]=="normalizar" for t in treino)
              and antes["acertos"] < antes["total"])
    candidato=avaliar(treino,True) if proposta else antes
    promover=bool(aprovar and proposta and candidato["acertos"]>antes["acertos"])
    if promover:
        memoria.guardar(usuario,"continuum_estrategia",CHAVE,
                        json.dumps({"habilitada":True,"origem":"aprovacao_explicita"}))
    inedito=avaliar(ineditas,ativa or promover)
    return {"treino_antes":antes,"treino_candidato":candidato,"inedito":inedito,
            "proposta":proposta,"promovida":promover,"estrategia_ativa":bool(ativa or promover),
            "limites":"Selecao de estrategia fixa pre-aprovada, nao aprendizado autonomo."}


def exemplos():
    return ([{"tipo":"normalizar","entrada":"  Bom   DIA ","esperado":"bom dia","grupo":"treino"},
             {"tipo":"somar","entrada":[2,3],"esperado":5,"grupo":"treino"}],
            [{"tipo":"normalizar","entrada":"  Ola   MUNDO ","esperado":"ola mundo","grupo":"inedito"},
             {"tipo":"somar","entrada":[9,1],"esperado":10,"grupo":"inedito"}])
