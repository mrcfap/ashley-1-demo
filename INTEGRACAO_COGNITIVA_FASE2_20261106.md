# Axyntora — integração cognitiva fase 2 (experimental)

## Implementado
- Fase 1: V17/V12/V41 com candidatos de memória sujeitos a revisão, persistência SQLite e testes.
- `app/core/provedor_cognitivo.py`: adaptador Gemini ou Ollama existente, selecionado por `AXYNTORA_COGNITIVE_PROVIDER`. Padrão `disabled`.
- `app/core/agencia_governada.py`: loop de planejamento/ação/observação para fila V22, com limite de passos, allowlist de ferramentas de leitura e política V74/MCP; não executa shell nem gravações.
- Testes unitários para execução autorizada, ferramenta bloqueada e limite de passos.

## NÃO homologado em produção
- Não há servidor MCP real conectado, nem autorização vinculada a hash/expiração para ações de escrita.
- Não foi configurado nem testado acesso real a Gemini/Ollama; faltam credenciais e serviços ativos no ambiente de execução.
- Não foi alterado o startup da API para disparar tarefas autonomamente; exige worker dedicado e implantação controlada.
- Não foram homologados todos os motores V1–V100, nem o deploy Render/Supabase.
- Não há autoedição ou autodeploy de código.

## Uso seguro
1. Executar `python -m pytest -q tests/test_agencia_governada.py tests/test_integrador_cognitivo.py tests/test_mcp_governance.py`.
2. Para consolidação, configurar `AXYNTORA_COGNITIVE_PROVIDER=gemini` com `GEMINI_API_KEY`, ou `ollama` com serviço Ollama local ativo. Nenhuma chamada é feita até invocar explicitamente `ProvedorCognitivo.gerar_texto`.
3. Instanciar `IntegradorCognitivo(db_path, ProvedorCognitivo(root))` num worker controlado. O SQLite é local: em Render efêmero, usar persistência durável antes de ativar.
4. Para tarefas, instanciar `AgenciaGovernada(fila, planejador, ferramentas={'nome': funcao_somente_leitura})`. O planejador deve devolver dict com `concluido` ou `ferramenta` e `argumentos`. Não cadastrar ferramentas de escrita nessa versão.
5. Fazer backup e testar em staging antes de substituir qualquer versão em produção.
