# Axyntora Continuum — integração experimental
Integração efetiva com PlannerAshley, CriticAshley e MemoriaLongoPrazo. Seleção de estratégia fixa de normalização após falha em treino, somente mediante aprovação explícita; avalia tarefas inéditas separadamente e persiste escolha na memória. Não treina modelos, não executa agentes web e não comprova aprendizagem autônoma.

Executar: `python -m pytest tests/test_continuum_integracao.py -q`.

Não colocar em produção como autoevolução; validar testes, isolamento, persistência PostgreSQL e políticas antes de expor endpoints. A versão principal do Render permanece preservada.
