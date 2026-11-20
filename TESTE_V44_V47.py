import asyncio
from app.operational_v44_v47 import OperationalExcellenceSuite

a=OperationalExcellenceSuite()
assert len(asyncio.run(a.initialize()))==4
x=asyncio.run(a.v44_sinapse.transfer_analogical_context('codigo','casos',{'patterns':['decomposicao']}))
assert x['status']=='success' and x['analogies'] and x['applied'] is False
assert a.v46_axiom.validate_action_alignment({'type':'delete_data'})['decision']=='requires_approval'
assert a.v46_axiom.validate_action_alignment({'type':'bypass_auth','approved_by_user':True})['decision']=='deny'
assert a.v46_axiom.validate_action_alignment({'type':'respond'})['aligned']
y=a.v47_maestria.deliberate('Criar um plano para reduzir atrasos',source_domain='codigo',domain='casos')
assert y['execution_performed'] is False and y['analogical_hypothesis']['analogies']
async def slow():
    await asyncio.sleep(0.1)
    return 1
async def test_timeout():
    assert await a.v45_nexus.execute_safe_async(slow(),fallback_value='fallback',timeout=.001)=='fallback'
    assert a.v45_nexus.get_health_status()['active_tasks_count']==0
asyncio.run(test_timeout())
print('OK: V44, V45, V46, V47 — testes locais concluídos')
