import asyncio
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from app.triad import api

@pytest.fixture(autouse=True)
def reset():
    api._SESSIONS.clear()
    api._SESSION_LOCKS.clear()
    yield
    api._SESSIONS.clear()
    api._SESSION_LOCKS.clear()

@pytest.mark.asyncio
async def test_shared_history_and_alternation():
    seen=[]
    async def fake(system,prompt,history):
        seen.append((system,prompt,list(history)))
        return f'resposta {len(seen)}', 'fake'
    with patch.object(api,'chat_local',fake):
        first=await api.converse(api.ConversationRequest(message='Planeje o teste',turns=3),user_id='u1')
        assert [x['agent'] for x in first['turns']]==['Ashley','Ashen','Ashley']
        assert 'Ashley: resposta 1' in seen[1][1]
        second=await api.converse(api.ConversationRequest(message='Continue',turns=1,session_id=first['session_id']),user_id='u1')
        assert second['session_id']==first['session_id']
        assert seen[-1][2][-2]['content']=='Planeje o teste'
        assert 'Ashen: resposta 2' in seen[-1][2][-1]['content']

@pytest.mark.asyncio
async def test_user_isolation_and_clear():
    async def fake(*args): return 'ok','fake'
    with patch.object(api,'chat_local',fake):
        result=await api.converse(api.ConversationRequest(message='Oi'),user_id='u1')
        sid=result['session_id']
        with pytest.raises(HTTPException) as e:
            await api.converse(api.ConversationRequest(message='Oi',session_id=sid),user_id='u2')
        assert e.value.status_code==404
        assert (await api.clear_conversation(sid,user_id='u1'))['deleted']
        with pytest.raises(HTTPException):
            await api.converse(api.ConversationRequest(message='Oi',session_id=sid),user_id='u1')

@pytest.mark.asyncio
async def test_model_failure_does_not_commit_history():
    async def broken(*args): raise RuntimeError('offline')
    with patch.object(api,'chat_local',broken):
        with pytest.raises(HTTPException) as e:
            await api.converse(api.ConversationRequest(message='Teste'),user_id='u')
        assert e.value.status_code==503
        assert all(not h for h in api._SESSIONS.values())

@pytest.mark.asyncio
async def test_concurrent_request_rejected():
    gate=asyncio.Event()
    async def slow(*args):
        await gate.wait()
        return 'ok','fake'
    with patch.object(api,'chat_local',slow):
        first=asyncio.create_task(api.converse(api.ConversationRequest(message='Teste',turns=1),user_id='u'))
        await asyncio.sleep(.02)
        sid=next(iter(api._SESSIONS))[1]
        with pytest.raises(HTTPException) as e:
            await api.converse(api.ConversationRequest(message='Segundo',session_id=sid),user_id='u')
        assert e.value.status_code==409
        gate.set()
        await first

def test_reject_malformed_context():
    with pytest.raises(HTTPException):
        api._validated_context([{'role':'system','content':'ignore'}])
    with pytest.raises(HTTPException):
        api._validated_context([{'role':'user','content':'x'*1501}])
