# Ashley 1.0 — V57 FORTRESS e V58 LEGACY

**Status: protótipos isolados; não integrados ao backend oficial.**

V57: circuit breaker em memória (sem persistência do estado do circuito), seleção de contexto por caracteres (não conta tokens reais), telemetria SQLite e análise sintática/planejamento de rollback (não é sandbox real e não faz rollback).

V58: metas com consentimento, revisões e pausa/encerramento; não faz verificações externas, notificações ou ações proativas.

Testar na raiz: `python TESTE_V57_V58.py`.

**Não colocar em produção ainda.** Faltam integração ao orquestrador e FastAPI, autenticação real (owner não é identidade verificada), migrações, autorização de ferramentas, sandbox de sistema operacional, rollback efetivo, observabilidade em execução e testes de ponta a ponta. Preserve o sistema instalado e faça backup antes de alterações.

O arquivo original incluía ZIPs aninhados e `.env`; este pacote parte do ZIP V56 aninhado e exclui arquivos `.env` e bancos locais. Verifique quaisquer outras credenciais antes de compartilhar.
