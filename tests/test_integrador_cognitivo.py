import asyncio
import json
import pytest
from app.core.integrador_cognitivo import IntegradorCognitivo

class FakeAI:
    async def gerar_texto(self, prompt):
        return json.dumps({'resumo':'Evento resumido; requer revisão.'})

def test_consolidacao_e_isolamento(tmp_path):
    hub = IntegradorCognitivo(tmp_path/'hub.db', FakeAI())
    hub.registrar('a','Tarefa A','Concluída')
    hub.registrar('b','Tarefa B','Falhou')
    assert asyncio.run(hub.consolidar('a')) == {'processados':1,'candidatas':1}
    assert len(hub.listar_candidatas('a')) == 1
    assert hub.listar_candidatas('b') == []
    assert asyncio.run(hub.consolidar('a'))['processados'] == 0
    assert asyncio.run(hub.consolidar('b'))['processados'] == 1

def test_rejeita_saida_invalida(tmp_path):
    class BadAI:
        async def gerar_texto(self, prompt): return '{"errado": true}'
    hub = IntegradorCognitivo(tmp_path/'hub.db', BadAI())
    hub.registrar('a','Evento','Resultado')
    with pytest.raises(ValueError):
        asyncio.run(hub.consolidar('a'))
    assert hub.listar_candidatas('a') == []
