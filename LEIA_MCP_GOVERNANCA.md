# Ashley — Fase 5: base de governança para MCP

Pacote incremental. Copie `app/` e `tests/` para a raiz da Ashley, sem remover outros arquivos.

## Teste

`python -m unittest discover -s tests -p "test_mcp_governance.py" -v`

## Escopo REAL

- Implementado: avaliação local *fail-closed*; lista explícita de ferramentas; classes de risco definidas no servidor; bloqueio sem autenticação; solicitações de escrita sempre exigem aprovação.
- Não implementado: cliente ou servidor MCP real; transporte stdio/HTTP; execução de ferramentas; OAuth; descoberta de servidores; persistência da auditoria; aprovação vinculada ao V22; UI; integração com o FastAPI principal.
- O arquivo `router.py` é uma estrutura **não montada**; não exponha a rota sem a autenticação real da Ashley.
- Nunca confiar em `requires_human_approval` informado por agente. Nunca considerar um `approved_action_id` suficiente sem validação e consumo no backend.
- Não ativar execução de comandos, navegação ou pagamentos antes de sandbox, autorização por escopo, auditoria persistente e testes de segurança.

## Próximas entregas

1. Descobrir a autenticação atual e criar adapter do usuario autenticado.
2. Persistir decisões e vincular aprovação de uso único ao V22 (usuário, ferramenta, hash dos argumentos, expiração).
3. Adicionar cliente MCP com servidores previamente autorizados e validação de origem/schema.
4. Integrar a política aos agentes da Fase 5 e painel de auditoria.
5. Testes integrados de permissões, revogação, replay, prompt injection e falhas de rede.
