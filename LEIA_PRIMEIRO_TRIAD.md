# Ashley 1.0 — MICD + MRIV + HORIZON (protótipo incremental)

Esta atualização **não** afirma que o diálogo entre modelos, a geração de widgets na interface ou a execução de agentes estejam prontos. Ela instala endpoints autenticados e testáveis, isolados do fluxo de chat atual.

## Instalação

1. Faça backup da pasta `Ashley Oficial final`.
2. Copie `app/triad/` desta atualização para `Ashley Oficial final/app/triad/`.
3. Abra `Ashley Oficial final/app/API/app.py` e acrescente **uma única vez**, ao final:

```python
from app.triad.api import router as triad_router
app.include_router(triad_router)
```

4. Reinicie o Uvicorn como normalmente faz. Entre na plataforma para obter uma sessão válida. Acesse `/docs` e teste as rotas `/api/v1/triad/*` com seu Bearer token **sem compartilhá-lo**.

## O que funciona nesta entrega

- `POST /api/v1/triad/micd/session`: ativa/desativa o modo dual e fornece configuração para turnos e papéis, mas ainda não gera falas reais.
- `POST /api/v1/triad/mriv/recommend`: sugere formato visual e soma valores numéricos, com verificação de rótulos. Não renderiza widgets no frontend.
- `POST /api/v1/triad/horizon/plan`: propõe roteamento local/externo, sem executar tarefas; ações externas sem aprovação ficam pendentes.
- `GET /api/v1/triad/status`: descreve limites e estado atual.

## Próxima integração

Conectar MICD ao serviço de modelo local, mantendo histórico separado por usuário e sessão, turno máximo e cancelamento; conectar MRIV a componentes frontend validados; conectar HORIZON ao orquestrador com permissões e auditoria. Testar primeiro em cópia e não em produção.
