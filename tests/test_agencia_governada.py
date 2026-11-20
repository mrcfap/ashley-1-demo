import asyncio
import pytest
from app.tasks.motor_execucao_v22 import MotorExecucaoV22
from app.core.agencia_governada import AgenciaGovernada, ExecucaoBloqueada

def test_execucao_leitura(tmp_path):
    fila = MotorExecucaoV22(tmp_path/'fila.db')
    t = fila.criar(user_id=1,titulo='Consulta',objetivo='Consultar dado')
    async def plano(obj, hist):
        return {'ferramenta':'consulta','argumentos':{'chave':'a'}} if not hist else {'concluido':True,'resposta':hist[-1]['observacao']}
    agente=AgenciaGovernada(fila,plano,{'consulta':lambda chave:{'chave':chave}})
    asyncio.run(agente.executar_proxima())
    assert fila.obter(t['id'])['status']=='CONCLUIDA'

def test_bloqueio_ferramenta_nao_autorizada(tmp_path):
    fila=MotorExecucaoV22(tmp_path/'fila.db')
    t=fila.criar(user_id=1,titulo='Bloqueio',objetivo='Não permitido',max_tentativas=1)
    async def plano(obj,hist): return {'ferramenta':'shell','argumentos':{'cmd':'echo hi'}}
    with pytest.raises(ExecucaoBloqueada):
        asyncio.run(AgenciaGovernada(fila,plano,{}).executar_proxima())
    assert fila.obter(t['id'])['status']=='FALHOU'

def test_limite_de_passos(tmp_path):
    fila=MotorExecucaoV22(tmp_path/'fila.db')
    t=fila.criar(user_id=1,titulo='Limite',objetivo='Loop',max_tentativas=1)
    async def plano(obj,hist):return {'ferramenta':'consulta','argumentos':{}}
    with pytest.raises(ExecucaoBloqueada):
        asyncio.run(AgenciaGovernada(fila,plano,{'consulta':lambda:'ok'},limite_passos=2).executar_proxima())
    assert fila.obter(t['id'])['status']=='FALHOU'
