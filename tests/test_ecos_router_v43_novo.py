import asyncio
import json
from pathlib import Path
import pytest
from app.core.ecos_v43_router import EcosV43Router
from app.evolution.motor_autoevolucao_v08 import MotorAutoEvolucaoV08

@pytest.mark.asyncio
async def test_cloud_fallback_local():
    async def cloud(**kw): raise RuntimeError('429')
    async def local(**kw): return 'local ok', 'qwen'
    r=EcosV43Router(cloud,local)
    out=await r.arbitrar_e_executar(system='s',message='m')
    assert out.provider=='local' and r.metrics['cloud_failure']==1

@pytest.mark.asyncio
async def test_private_never_cloud():
    calls=[]
    async def cloud(**kw): calls.append('cloud');return 'x','x'
    async def local(**kw): calls.append('local');return 'ok','qwen'
    r=EcosV43Router(cloud,local)
    assert (await r.arbitrar_e_executar(system='',message='',private=True)).provider=='local'
    assert calls==['local']

@pytest.mark.asyncio
async def test_local_first_fallback():
    async def cloud(**kw): return 'cloud ok','gemini'
    async def local(**kw): raise RuntimeError('offline')
    r=EcosV43Router(cloud,local,local_first=True)
    assert (await r.arbitrar_e_executar(system='',message='')).provider=='cloud'

@pytest.mark.asyncio
async def test_circuit_recovers():
    attempts=[0]
    async def cloud(**kw):
        attempts[0]+=1
        if attempts[0]==1: raise RuntimeError('429')
        return 'ok','gemini'
    async def local(**kw): return 'ok','qwen'
    r=EcosV43Router(cloud,local,max_failures=1,cooldown=0)
    await r.arbitrar_e_executar(system='',message='')
    assert (await r.arbitrar_e_executar(system='',message='')).provider=='cloud'

@pytest.mark.asyncio
async def test_evolution_proposal_no_execution(tmp_path):
    class AI:
        async def gerar_texto(self,p):
            return json.dumps({'codigo_fonte':'def f():\n    return 1','codigo_teste':'def test_f():\n    assert f()==1'})
    m=MotorAutoEvolucaoV08(AI(),tmp_path)
    out=await m.propor_capacidade('fazer f','f')
    assert out['estado']=='AGUARDANDO_SANDBOX_E_APROVACAO'
    assert (Path(out['pasta'])/'proposta.py.txt').exists()
    assert not (Path(out['pasta'])/'f.py').exists()

@pytest.mark.asyncio
async def test_evolution_reject_bad_identifier(tmp_path):
    class AI: pass
    with pytest.raises(ValueError):
        await MotorAutoEvolucaoV08(AI(),tmp_path).propor_capacidade('x','../../bad')
