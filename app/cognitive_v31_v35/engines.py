"""V31-V35: mecanismos heurísticos auditáveis, sem execução autônoma de código."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
import sqlite3
from pathlib import Path


def _trim(value, n=2000):
    return str(value or "")[:n]

class MACIEngine:
    """Classificação conservadora de intenção; não diagnostica emoções."""
    def analisar_e_alinhar(self, user_input, contexto_longo=""):
        s=_trim(user_input).lower()
        if any(x in s for x in ("erro", "falha", "não funciona", "corrigir", "bug", "traceback")):
            intent, mode="diagnostico", "analitico"
        elif any(x in s for x in ("crie", "implemente", "construa", "gere", "faça")):
            intent, mode="execucao_solicitada", "objetivo"
        elif any(x in s for x in ("ideia", "imagine", "inove", "criativ")):
            intent, mode="exploracao", "criativo"
        elif "?" in s or any(x in s for x in ("explique", "como ", "por que")):
            intent, mode="esclarecimento", "didatico"
        else:
            intent, mode="conversa", "equilibrado"
        return {"intencao_inferida":intent,"modo_recomendado":mode,"confianca":"heuristica_baixa", "contexto_longo_consultado":bool(contexto_longo),"nota":"Inferência revisável; não representa leitura emocional ou intenção oculta."}

class MECAEngine:
    """Contra-argumentação condicional, sem inventar defeitos concretos."""
    def avaliar(self, plano, historico=None):
        texto=_trim(plano, 2500)
        perguntas=["Que evidências sustentam a hipótese central?", "Qual alternativa mais simples atende ao objetivo?", "Quais dependências e consequências não foram verificadas?"]
        hist=[_trim(x,500) for x in (historico or [])[-3:]]
        loop=len(hist)==3 and len(set(hist))==1
        return {"status":"revisao_sugerida", "plano_avaliado":texto[:300], "questoes_criticas":perguntas,"repeticao_detectada":loop,"alternativa":"Testar solução menor e reversível antes de expandir.","afirmacoes_de_falha_comprovadas":False}

class MEMOEngine:
    """Metadados de retenção separados das tabelas legadas; sem exclusão automática."""
    def __init__(self, db_path):
        self.db_path=str(db_path)
        with sqlite3.connect(self.db_path, timeout=10) as c:
            c.execute("CREATE TABLE IF NOT EXISTS v33_memoria_politica (user_id INTEGER NOT NULL, referencia TEXT NOT NULL, importancia REAL NOT NULL DEFAULT 0.5, protegida INTEGER NOT NULL DEFAULT 1, ultima_ativacao TEXT, PRIMARY KEY(user_id,referencia))")
    def avaliar_retencao(self, user_id, referencia, importancia=0.5, protegida=True):
        if not 0<=float(importancia)<=1:raise ValueError("importancia fora do intervalo")
        return {"user_id":int(user_id),"referencia":_trim(referencia,120),"importancia":float(importancia),"protegida":bool(protegida),"acao":"preservar" if protegida else "revisao_manual","exclusao_automatica":False}
    def consolidacao_onirica(self, user_id):
        return {"user_id":int(user_id),"estado":"avaliacao_disponivel","memorias_excluidas":0,"nota":"Consolidação real requer revisão de dados e autorização; não executada."}

class QDEAEngine:
    """Recomenda parâmetros; o provedor decide quais suporta."""
    def modular_estado(self, complexidade_tarefa, travado_em_loop=False):
        if travado_em_loop: modo, temp, profundidade="exploracao_alternativa",0.7,5
        elif complexidade_tarefa=="alta":modo,temp,profundidade="revisao_critica",0.2,6
        else:modo,temp,profundidade="resposta_direta",0.3,2
        return {"modo_operacional":modo,"temperatura_sugerida":temp,"profundidade_planejamento_sugerida":profundidade,"parametros_aplicados_ao_provedor":False,"nota":"Não representa consciência ou mudança automática de modelo."}

class V35EvidenciasGovernanca:
    """Verifica limites de afirmações e de execução antes da resposta."""
    def avaliar(self, mensagem, meca=None):
        s=_trim(mensagem).lower()
        sensivel=any(x in s for x in ("apague", "delete", "publique", "envie dinheiro", "instale", "modifique o código", "execute código"))
        return {"exige_autorizacao_para_acao_externa":sensivel,"execucao_externa_autorizada":False,"nivel_evidencia":"heuristico_sem_verificacao_externa","regra":"Não afirmar execução, validação, sentimentos ou certeza sem evidência; pedir aprovação antes de ações sensíveis.","contraponto_disponivel":bool(meca)}

class CognitiveV31V35:
    def __init__(self, db_path):
        self.db_path=str(db_path)
        self.v31=MACIEngine();self.v32=MECAEngine();self.v33=MEMOEngine(db_path);self.v34=QDEAEngine();self.v35=V35EvidenciasGovernanca()
        with sqlite3.connect(self.db_path,timeout=10) as c:
            c.execute("CREATE TABLE IF NOT EXISTS v31_v35_auditoria (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, criado TEXT NOT NULL, intencao TEXT NOT NULL, modo TEXT NOT NULL)")
    def analisar(self, mensagem, user_id, contexto="", registrar=False):
        maci=self.v31.analisar_e_alinhar(mensagem, contexto)
        complexidade="alta" if len(_trim(mensagem))>300 or maci["intencao_inferida"]=="diagnostico" else "baixa"
        qdea=self.v34.modular_estado(complexidade)
        meca=self.v32.avaliar(mensagem) if complexidade=="alta" else None
        v35=self.v35.avaliar(mensagem,meca)
        if registrar:
            with sqlite3.connect(self.db_path,timeout=10) as c:
                c.execute("INSERT INTO v31_v35_auditoria(user_id,criado,intencao,modo) VALUES(?,?,?,?)",(int(user_id),datetime.now(timezone.utc).isoformat(),maci["intencao_inferida"],qdea["modo_operacional"]))
        return {"v31_maci":maci,"v32_meca":meca or {"estado":"nao_acionado"},"v33_memo":{"estado":"politica_de_retencao_disponivel","exclusao_automatica":False},"v34_qdea":qdea,"v35_governanca":v35}
    def instrucoes(self, analise):
        return ("MOTORES V31-V35 (análise heurística executada no backend; não invente execução externa):\n"+
                json.dumps(analise,ensure_ascii=False,default=str)[:3500]+
                "\nAdapte clareza e profundidade ao pedido. Críticas são perguntas a verificar, não defeitos comprovados. "
                "Não afirme que temperatura foi aplicada ao provedor. Não afirme que memórias foram apagadas. "
                "Os motores V31-V35 são heurísticos integrados ao chat; seus resultados não provam consciência nem autonomia irrestrita.")
    def status(self):
        return {"v31":"classificacao heuristica de intencao integrada ao chat", "v32":"contraponto condicionado a complexidade", "v33":"politica de memoria conservadora, sem exclusao automatica", "v34":"selecao de modo operacional; temperatura apenas sugerida", "v35":"governanca e limites de evidencia; sem executar acoes externas"}
