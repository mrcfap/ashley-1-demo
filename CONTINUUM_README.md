# Axyntora Continuum — primeira etapa

Implementação inicial de benchmark offline determinístico com histórico SQLite, separação de treino e tarefas inéditas, taxa de sucesso e duração. Não implementa aprendizado autônomo, navegação web ou melhoria de modelos. Não divulgar resultados sintéticos como desempenho real da Ashley.

Teste: `python -m pytest tests/test_continuum_benchmark.py -q`.

Próximas fases: integrar planner, critic e memória; criar 100 tarefas reais com baseline; avaliar recuperação após reinício; auditoria e validação humana; testar em ambiente isolado antes de deploy no Render.
