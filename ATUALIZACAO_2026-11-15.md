# Atualização incremental — 15/11/2026
- Adicionado seletor visual de idioma em quatro páginas de entrada, com preferência local e evento `ashley:language-change`.
- Adicionado núcleo experimental de propostas evolutivas `app/evolution/governed_evolution.py`: cria propostas para revisão, sem executar patches ou modificar produção.
- Adicionados testes unitários `tests/test_governed_evolution_addon.py`.
- **Limitações:** seletor ainda não conecta automaticamente o idioma ao backend/TTS; não há cobrança, planos ativos nem integração de pagamentos. O núcleo evolutivo não cria agentes autonomamente nem implanta alterações; é a primeira etapa segura.
- Próximas etapas: integrar seleção ao fluxo de chat/TTS, autenticação e preferências por usuário; definir planos sem preços; construir avaliação em sandbox, revisão humana, auditoria e rollback.
- Segurança: manter arquivos .env e bancos de dados fora de distribuição pública. Não implantar o ZIP diretamente em hospedagem pública.
