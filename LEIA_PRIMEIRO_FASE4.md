# Ashley — Fase 4 (ponte V22)

1. Faça backup da pasta oficial e pare o Uvicorn.
2. Extraia este ZIP **na raiz do projeto**, preservando a estrutura `app/` e `tests/`. Não substitua `app.py` nem `motor_execucao_v22.py`.
3. No PowerShell, execute: `python -m unittest discover -s tests -p "test_phase4.py" -v`.

## Limites desta entrega

A ponte registra missões na fila V22 em banco **separado** `ashley_coding_v22.db` para não interferir nas tarefas existentes. A aprovação é para **gerar proposta**, nunca para publicar código. A execução é explicitamente invocada via `run_approved`; não há worker automático nem endpoint web nesta fase. A integração real com Gemini depende de credenciais e cotas e ainda precisa ser testada no ambiente do usuário. A revisão estática não é sandbox; nenhum código gerado é executado.

## Exemplo de uso (sem chamar Gemini)

```python
from app.agents.autonomous.phase4 import CodingV22Bridge
bridge = CodingV22Bridge('.')
tarefa = bridge.submit(1, 'Melhorar clareza do módulo', ['app/agents/planner.py'])
print(tarefa['id'])
# Para autorizar SOMENTE a geração da proposta:
# bridge.approve_generation(tarefa['id'], 1)
# import asyncio
# relatorio = asyncio.run(bridge.run_approved(tarefa['id'], 1))
```

**Atenção:** não exponha `approve_generation` e `run_approved` como rotas públicas sem autenticação, autorização por usuário e proteção contra abuso. Não utilize o relatório como autorização para implantar alterações.
