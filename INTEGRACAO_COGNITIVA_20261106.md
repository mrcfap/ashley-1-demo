# Integração cognitiva incremental — 06/11/2026

## Implementado
- `app/core/integrador_cognitivo.py`: armazenamento SQLite de eventos V17, consolidação V12 por provedor de inferência injetado e candidatos de memória V41.
- Isolamento por usuário, limite de lote, validação do JSON, gravação transacional e status `PENDENTE_REVISAO` para evitar transformar inferências em fatos.
- `tests/test_integrador_cognitivo.py`: testes de isolamento, idempotência e rejeição de respostas inválidas.

## Integração deliberadamente não ativada em produção
- Nenhuma tarefa de background foi adicionada ao FastAPI. Em Render, a consolidação deve rodar em worker único, com configuração explícita e monitoramento.
- Não há conexão automática entre candidatos de memória e prompts de conversa; é necessária uma política de revisão e consentimento.
- Não foi habilitada execução externa MCP nem autoedição/deploy de código. V68/V74 permanecem fail-closed.
- O adaptador `ai_service` deve implementar `async gerar_texto(prompt) -> str`.

## Testes executados
`python -m pytest -q tests/test_integrador_cognitivo.py tests/test_mcp_governance.py`
Resultado: 7 passed.

## Próximos passos
1. Integrar ao serviço de inferência existente, sem alterar assinaturas públicas.
2. Definir política de consentimento, retenção e aprovação das memórias.
3. Criar worker com lock/lease persistente, observabilidade e limites de custo.
4. Integrar V22/V68/V74 com ferramentas em allowlist e aprovações vinculadas a argumentos.
5. Rodar suíte completa e homologação de API antes de qualquer deploy.
