# Evolução contínua supervisionada — Ashley

O ciclo coleta **métricas fornecidas explicitamente em JSON**, avalia quatro indicadores e gera propostas de revisão. **Não mede automaticamente a API, não altera código, não inicia processos de fundo e não implanta mudanças.**

Exemplo de arquivo `metricas.json`:
```json
{"vision_latency_ms": 1800, "language_mismatch_rate": 0.04, "memory_recall_rate": 0.80, "response_latency_ms": 3500}
```

Na raiz do projeto:
```powershell
python -m app.evolution.evolution_cycle --root . --metrics metricas.json
python -m pytest tests/test_evolution_cycle.py -q
```

Resultados ficam em `.ashley_evolution_reviews/` com propostas `pending_human_review` e trilha `cycle_audit.jsonl`. Pode-se agendar o comando no Windows Task Scheduler **apenas após** configurar a geração confiável das métricas e aprovação do responsável. Nenhuma proposta é aplicada automaticamente. Métricas não devem conter dados pessoais ou segredos. Os limiares são iniciais e precisam de calibração com medições reais.

## Próxima integração
Instrumentar os endpoints reais para coletar métricas agregadas, sem dados pessoais; criar painel de revisão; adicionar autorização administrativa e testes de integração antes de permitir qualquer implantação.
