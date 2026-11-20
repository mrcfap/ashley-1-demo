"""V27-V30: motores experimentais locais. Sem execução externa automática."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, sqlite3, time, math, struct

class Repositorio:
    def __init__(self, db): self.db=str(db)
    def registrar(self, user_id, motor, tipo, payload):
        # Conexão sempre fechada antes de retornar (compatibilidade Windows).
        con=sqlite3.connect(self.db, timeout=5)
        try:
            con.execute('CREATE TABLE IF NOT EXISTS v27_v30_eventos (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, motor TEXT NOT NULL, tipo TEXT NOT NULL, payload TEXT NOT NULL, criado REAL NOT NULL)')
            cur=con.execute('INSERT INTO v27_v30_eventos(user_id,motor,tipo,payload,criado) VALUES(?,?,?,?,?)',(int(user_id),motor,tipo,json.dumps(payload,ensure_ascii=False),time.time()))
            con.commit()
            return cur.lastrowid
        finally: con.close()

class V27Iniciativa:
    def sugerir(self, objetivo, pendencias, autorizado=False):
        if not autorizado: return {'ativo':False,'motivo':'opt_in_necessario','sugestoes':[]}
        itens=[str(x).strip()[:180] for x in pendencias if str(x).strip()][:5]
        return {'ativo':True,'objetivo':str(objetivo)[:300], 'sugestoes':[{'pendencia':x,'proxima_acao':'Confirmar prioridade e preparar plano de resolução','executada':False} for x in itens], 'requer_aprovacao':True}

class V28Musica:
    def gerar_musica_completa(self, *, titulo, letra, estilo='rock', voz='masculina', duracao_segundos=180, bpm=100, tom='Am', prompt_extra='', endpoint=None, api_key=None, pasta_saida='data/generated/music'):
        """Delega a geração real ao provedor configurado; nunca simula áudio gerado."""
        from app.music.producao import ProducaoMusicalV28
        return ProducaoMusicalV28(endpoint=endpoint, api_key=api_key, pasta_saida=pasta_saida).gerar(
            titulo=titulo, letra=letra, estilo=estilo, voz=voz,
            duracao_segundos=duracao_segundos, bpm=bpm, tom=tom,
            prompt_extra=prompt_extra,
        )

    def projeto(self, tema, estilo='rock', bpm=100, tom='Am'):
        bpm=int(bpm)
        if not 40<=bpm<=220:raise ValueError('BPM deve ficar entre 40 e 220')
        return {'tema':str(tema)[:500], 'estilo':str(estilo)[:80], 'bpm':bpm,'tom':str(tom)[:16], 'estrutura':['intro','verso 1','refrão','verso 2','refrão','ponte','solo','refrão final'], 'status':'briefing_pronto', 'audio_gerado':False, 'observacao':'Para canção cantada e mixada é necessário integrar provedor de geração musical licenciado.'}
    def midi_guia(self, destino, notas=(60,64,67,72), bpm=100):
        """Cria MIDI instrumental monofônico original, sem dependências externas."""
        bpm=int(bpm)
        if not 40<=bpm<=220:raise ValueError('BPM inválido')
        notas=list(notas)
        if len(notas)>512 or any(not isinstance(n,int) or not 0<=n<=127 for n in notas):raise ValueError('Notas MIDI inválidas')
        def vlq(v):
            a=[v&127];v>>=7
            while v:a.insert(0,(v&127)|128);v>>=7
            return bytes(a)
        tr=b'\x00\xff\x51\x03'+int(60000000/bpm).to_bytes(3,'big')
        for n in notas:tr+=b'\x00'+bytes([0x90,n,85])+vlq(480)+bytes([0x80,n,0])
        tr+=b'\x00\xff\x2f\x00'
        data=b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk'+struct.pack('>I',len(tr))+tr
        dest=Path(destino);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        return {'arquivo':str(dest),'bytes':len(data),'tipo':'audio/midi'}

class V29Inovacao:
    def avaliar(self, ideia, novidade, utilidade, viabilidade, risco):
        vals=[novidade,utilidade,viabilidade,risco]
        if any(not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=5 for x in vals):raise ValueError('Critérios devem estar entre 0 e 5')
        score=round((novidade*.25+utilidade*.35+viabilidade*.4)-risco*.25,2)
        return {'ideia':str(ideia)[:500], 'pontuacao_heuristica':score, 'criterios':dict(novidade=novidade,utilidade=utilidade,viabilidade=viabilidade,risco=risco),'originalidade_verificada':False,'proxima_etapa':'Pesquisar soluções existentes e testar hipótese com evidências','decisao_automatica':False}

class V30LaboratorioFuturos:
    def simular(self, valor_inicial, cenarios, anos=5):
        """Projeções matemáticas condicionais; NÃO são previsões."""
        if not isinstance(valor_inicial,(int,float)) or not math.isfinite(valor_inicial) or valor_inicial<0:raise ValueError('Valor inicial inválido')
        if not isinstance(anos,int) or not 1<=anos<=20:raise ValueError('Horizonte inválido')
        if not isinstance(cenarios,list) or not 1<=len(cenarios)<=6:raise ValueError('Informe 1 a 6 cenários')
        resultados=[]
        for c in cenarios:
            nome=str(c['nome'])[:80];taxa=float(c['taxa_anual'])
            if not math.isfinite(taxa) or not -0.95<=taxa<=3:raise ValueError('Taxa fora do intervalo')
            serie=[round(valor_inicial*((1+taxa)**a),2) for a in range(anos+1)]
            resultados.append({'nome':nome,'taxa_assumida':taxa,'serie':serie})
        return {'tipo':'simulacao_condicional','nao_e_previsao':True,'anos':anos,'valor_inicial':valor_inicial,'cenarios':resultados,'limitacoes':['Taxas são hipóteses fornecidas, não estimativas estatísticas','Não inclui inflação, impostos, custos ou choques externos salvo modelados explicitamente']}

class MotoresV27V30:
    def __init__(self,db):
        self.repo=Repositorio(db);self.v27=V27Iniciativa();self.v28=V28Musica();self.v29=V29Inovacao();self.v30=V30LaboratorioFuturos()
    def status(self):
        return {'v27':'sugestões com opt-in, sem agendamento automático','v28':'briefing e guia MIDI, sem voz cantada ou áudio produzido','v29':'avaliação heurística, sem pesquisa de originalidade automática','v30':'simulação condicional com hipóteses explícitas, sem previsão do futuro'}
