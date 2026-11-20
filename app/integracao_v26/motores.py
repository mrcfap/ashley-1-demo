"""V23-V26: coordenação conservadora, sem diagnósticos ou leitura de emoções."""
from __future__ import annotations
import json, sqlite3, time
from pathlib import Path

PRINCIPIOS = ("Não fingir consciência ou emoções humanas", "Não diagnosticar pessoas", "Respeitar consentimento e privacidade", "Não alterar código ou permissões sem aprovação", "Corrigir interpretações quando o usuário discordar")

class V23Identidade:
    def __init__(self, db): self.db = str(db)
    def inicializar(self):
        with sqlite3.connect(self.db) as con:
            con.execute("CREATE TABLE IF NOT EXISTS v23_avaliacoes (id INTEGER PRIMARY KEY, user_id INTEGER, criado_em REAL, categoria TEXT, resultado TEXT, aprovado INTEGER DEFAULT 0)")
    def registrar(self, user_id, categoria, resultado):
        self.inicializar()
        with sqlite3.connect(self.db) as con:
            cur=con.execute("INSERT INTO v23_avaliacoes(user_id,criado_em,categoria,resultado) VALUES (?,?,?,?)",(user_id,time.time(),categoria,json.dumps(resultado,ensure_ascii=False)))
            return cur.lastrowid
    def principios(self): return list(PRINCIPIOS)

class V24PsicologiaRelacional:
    def avaliar(self, texto):
        texto=(texto or '').lower()
        # Sinais linguísticos explícitos; não infere condição clínica.
        termos={'pedido_apoio':('preciso conversar','me ajuda','estou triste','estou com medo','estou nervoso','estou esgotado'), 'pedido_objetivo':('passo a passo','me explique','como faço','me ensina')}
        sinais=[nome for nome,expressoes in termos.items() if any(e in texto for e in expressoes)]
        return {'sinais_declarados':sinais,'diagnostico':None,'instrucao':'Acolha sem diagnosticar; pergunte antes de interpretar emoções; preserve autonomia do usuário.'}

class V25PercepcaoMultimodal:
    def analisar(self, *, consentimento=False, voz=None, visual=None):
        if not consentimento: return {'ativo':False,'motivo':'consentimento_necessario','observacoes':[]}
        obs=[]
        if isinstance(voz,dict):
            for campo in ('ritmo','volume','pausas','variacao_tom'):
                if campo in voz: obs.append({'origem':'voz','sinal':campo,'valor':str(voz[campo])[:100]})
        if isinstance(visual,dict):
            for campo in ('sobrancelhas','olhar','boca','movimento'):
                if campo in visual: obs.append({'origem':'visual','sinal':campo,'valor':str(visual[campo])[:100]})
        return {'ativo':True,'observacoes':obs,'emocao_inferida':None,'nota':'Sinais observáveis não comprovam emoções; confirmar com a pessoa.'}

class IntegradorV26:
    def __init__(self,db):
        self.v23=V23Identidade(db); self.v24=V24PsicologiaRelacional(); self.v25=V25PercepcaoMultimodal()
    def preparar(self,texto,*,consentimento_multimodal=False,voz=None,visual=None):
        rel=self.v24.avaliar(texto)
        percepcao=self.v25.analisar(consentimento=consentimento_multimodal,voz=voz,visual=visual)
        prompt=("INTEGRAÇÃO V23-V26: mantenha identidade operacional estável, honestidade, contexto e memória autorizada. "
                "Raciocine e planeje, utilize ferramentas reais somente quando disponíveis. "
                "Respeite consentimento, idade e limites de segurança. Não alegue ter analisado voz ou rosto sem dados fornecidos. "
                "Não diagnostique nem deduza emoções pela aparência ou entonação. "
                "V24 sinais de linguagem explícita: "+json.dumps(rel['sinais_declarados'],ensure_ascii=False)+". "
                "V25 observações autorizadas: "+json.dumps(percepcao['observacoes'],ensure_ascii=False)+". "
                "Se houver ambiguidade emocional, pergunte à pessoa.")
        return {'prompt':prompt,'v24':rel,'v25':percepcao,'v23':{'principios':self.v23.principios()},'capacidades':['linguagem','raciocinio','contexto','memoria','visao','voz','ferramentas','seguranca']}
