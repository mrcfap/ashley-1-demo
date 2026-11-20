# Axyntora / Ashley 1.0 — testes rápidos de integração

## Origem
Pacote: Axyntora_Ashley_V43_V08_integrados_20261106.zip. Verificações em cópia isolada, sem modificar instalação local ou Render.

## Resultado
- 24 testes direcionados aprovados (integração cognitiva, crescimento supervisionado, roteador ECOS V43, governança MCP e endurecimento V22).
- Compilação Python dos módulos `app/core/ecos_v43_router.py`, `app/core/integrador_cognitivo.py`, `app/evolution/motor_autoevolucao_v08.py` e `app/API/app.py` concluída sem erros de sintaxe.
- Suíte completa interrompida na coleta de `tests/test_phase2.py`: falta dependência `google-genai` no ambiente desta execução (`ImportError: cannot import name 'genai' from 'google'`).

## Limites da validação
Não foram feitas chamadas reais aos provedores Gemini/Ollama, execução em sandbox de SO, teste de cliente MCP remoto, teste ponta a ponta com banco real ou publicação na Render. A flag `ASHLEY_HYBRID_ROUTER_ENABLED` permanece desativada por padrão. A aprovação de 24 testes não significa homologação integral.

## Orientação
Testar em ambiente de staging com dependências instaladas, credenciais apropriadas e serviços reais antes de habilitar roteamento híbrido em produção. Preservar dados, credenciais e configuração existentes.
