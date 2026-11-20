# Ashley V66–V70 e V73–V75 — pacote incremental

**Inclui oito motores:** V66 ALETHEIA (avaliação conservadora de evidências), V67 CHRONOS-FLOW (propostas de agenda), V68 OMNI-BRIDGE (catálogo MCP), V69 ETHOS-GUARD (permissões por escopo), V70 IMPACT-LEGACY (planejamento social), V73 TRACE-LINK (trilha de auditoria com digest), V74 SAFE-HARBOR (bloqueio de ações arriscadas), V75 RELEASE-GATE (checklist de prontidão).

**V71 e V72 não são sobrescritos.** São oito motores novos, completando o escopo até V75.

## Instalação

1. Pare o Uvicorn e faça backup do projeto.
2. Extraia o ZIP na raiz `Ashley Oficial final`, preservando a estrutura `app/`, `tests/`.
3. Execute `python -m unittest discover -s tests -p "test_v66_v75.py" -v`.
4. Se os testes passarem, execute `python INSTALAR_V66_V75.py`.
5. Reinicie o Uvicorn e confira `/docs` para as rotas `/api/v1/engines/v66/...` até `/v75/...`.

## Limites e próximos passos

- Os motores são uma **base funcional incremental**, não uma integração final ao chat, V22, voz, agenda ou ERP.
- V66 **não** oferece garantia de erro zero nem verificação independente automática. Não use relatórios oficiais sem revisão humana.
- V67 **não** altera compromissos reais.
- V68 **não** faz chamadas MCP reais; catálogo de conectores é etapa preparatória.
- V69 não constitui certificação LGPD/GDPR; autorização humana e auditoria de segurança continuam necessárias.
- V70 não declara impacto social sem evidência externa.
- V73 grava digest de eventos, mas não fornece cadeia criptográfica inviolável.
- V74 é somente avaliação preventiva; execução de ferramentas requer integração posterior.
- V75 é autoavaliação de campos enviados, não auditoria de produção.
- A API reutiliza a dependência de autenticação adulta `app.integrations.v62_v65_api.identity` e separa dados pelo identificador autenticado.
- Testes unitários incluídos; testes de API com autenticação real e integração de produção ainda são necessários.
