# Axyntora — arquitetura de evolução contínua supervisionada

Novo módulo: `app/evolution/continuous_agent_architecture.py`.

Ciclo: observador -> analista -> arquiteto -> ética/privacidade -> testador -> revisão humana.
O módulo registra hipóteses, benefício esperado, plano de teste e risco em `.ashley_evolution_reviews/` (gerado quando utilizado). Propostas de código são apenas documentos: **não são executadas nem promovidas automaticamente**.

Exemplo de uso programático:

```python
from app.evolution.continuous_agent_architecture import ContinuousEvolution
motor = ContinuousEvolution('.')
motor.observe('vision_latency', 'Atraso na resposta da câmera',
              'Fila de processamento excessiva', 'Reduzir latência',
              'Comparar p50/p95 antes e depois em ambiente isolado')
print(motor.list_pending())
```

A arquitetura **não está ligada a um agendador**: não há autoexecução contínua em segundo plano, nem novos agentes gerados automaticamente. Para operacionalizar, integrar um orquestrador agendado com limites, métricas, consentimento, aprovação humana e testes isolados. Componentes protegidos continuam sujeitos a revisão externa. Não há alegação de consciência, sentimentos ou evolução autônoma sem supervisão.

Testes novos: `tests/test_continuous_agent_architecture.py`.
