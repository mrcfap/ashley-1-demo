# Integração segura: agentes + prompts + memória

Módulo opt-in: `app/agents/agent_prompt_memory_bridge.py`.

Fornece prompts especializados versionados para os seis papéis de evolução, busca de memória por `user_id` e criação de propostas auditáveis usando o mecanismo de revisão humana existente.

Exemplo (executar em ambiente autorizado):

```python
from app.memory.memoria_longa import MemoriaLongoPrazo
from app.agents.agent_prompt_memory_bridge import build_context, propose_with_context
memory = MemoriaLongoPrazo("data/memoria.sqlite3")
context = build_context("analista", user_id=123, query="latência", memory=memory)
# O contexto pode ser enviado a um modelo por um orquestrador confiável, com consentimento.
# propose_with_context(...) registra proposta para revisão, sem aplicar patches.
```

**Limites:** não liga automaticamente a API, não agenda tarefas, não invoca LLM, não aplica alterações nem garante isolamento de todo o restante do sistema. O armazenamento de memória existente precisa de auditoria independente, especialmente no PostgreSQL. Não enviar dados pessoais em logs ou propostas. Testes unitários não substituem testes ponta a ponta e de segurança.
