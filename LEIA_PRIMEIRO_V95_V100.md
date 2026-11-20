# AXYNTORA — Pacote incremental V95–V100

Base exata: `Ashley Oficial final(20261018-163222).zip` enviada nesta conversa.

## Instalação Windows

1. Pare Uvicorn com Ctrl+C e faça backup completo da pasta `Ashley Oficial final`.
2. Extraia este ZIP na **raiz** dessa pasta, mantendo diretórios `app/...` e `tests/...`. Substitua os arquivos existentes quando solicitado.
3. Execute:

   `python -m pytest tests/test_v95_v100.py tests/test_v85_v94.py tests/test_v84_v94_bridge.py -q`

4. Execute:

   `python -m uvicorn app.API.app:app --reload`

5. Entre no sistema, acesse `/docs` e procure `Axyntora V95-V100`.
6. Consulte `GET /api/v1/engines/v84/integration-catalog`: intervalo esperado `V1-V100`.

## Arquivos alterados

- `app/API/app.py` — registro do router autenticado V95–V100.
- `app/nextgen/nextgen_planning.py` — inventário e seleção heurística dos 16 motores V85–V100.
- `app/nextgen/symphony_bridge.py` — catálogo expandido para V85–V100.
- `app/axiom_v95_v100/{__init__,core,api}.py` — motores novos.
- `tests/test_v95_v100.py` — 16 testes novos.
- `tests/test_v84_v94_bridge.py` — 5 testes anteriores adaptados ao inventário V1–V100.

## APIs autenticadas (Bearer do sistema existente)

- `GET /api/v1/engines/v95-v100/catalog`
- `POST /api/v1/engines/v95/affective-state` — `{"data":{"consent":true,"preferred_tone":"acolhedor"}}`
- `POST /api/v1/engines/v95/voice-synthesis/adaptive` — devolve **perfil**, não áudio.
- `POST /api/v1/engines/v96/proactive/trigger` — `{"data":{"consent":true,"context":"Tenho testes pendentes","suggested_action":"Executar testes"}}`
- `GET /api/v1/engines/v96/proposals`
- `POST /api/v1/engines/v96/proposals/{id}/review?approved=true` — aprovação apenas documental; **não executa**.
- `POST /api/v1/engines/v97/narrative/event` — `{"data":{"consent":true,"title":"Marco","description":"Fato relatado","source":"relato do usuário"}}`
- `GET /api/v1/engines/v97/narrative/arc`
- `DELETE /api/v1/engines/v97/narrative/event/{id}`
- `POST /api/v1/engines/v98/investigations` — `{"data":{"question":"Pergunta","sources":[{"title":"Fonte","excerpt":"Trecho"}]}}`
- `GET /api/v1/engines/v98/investigations/{id}`
- `POST /api/v1/engines/v99/improvements/propose` — `{"data":{"title":"Correção","candidate_code":"print(1)"}}`
- `GET /api/v1/engines/v99/improvements/{id}`
- `POST /api/v1/engines/v100/mission` — `{"data":{"objective":"Pesquisar evidências e corrigir código"}}`
- `GET /api/v1/engines/v100/mission/{id}`
- `GET /api/v1/engines/v100/system-health`

O `user_id` é obtido do token; nunca de parâmetros do usuário. Registros SQLite: `data/v95_v100.db`.

## Limitações técnicas importantes

- **V95**: adaptação apenas por preferência declarada e consentimento; não há leitura biométrica, inferência de emoções nem TTS neural gerado.
- **V96**: propostas persistentes e deduplicadas; não há observação de agenda, notificações nem tarefa automática em segundo plano.
- **V97**: linha do tempo com fatos informados, proveniência e exclusão; síntese simples, sem análise semântica de meses de conversa.
- **V98**: dossiê de fontes fornecidas; **não faz pesquisa na internet nem valida as fontes externamente**.
- **V99**: aceita código candidato e verifica sintaxe/flags estáticas; **não programa autonomamente, não executa testes em sandbox, não aplica patches nem implanta em produção**.
- **V100**: missões persistentes, seleção heurística e trilha de planejamento; **não executa agentes nem opera autonomamente**.
- Os seis motores estão integrados ao inventário e planejamento do V84; **não há despacho automático no `/chat`**, nem processamento real de áudio/vídeo.
- Esta entrega é uma base funcional limitada para evolução supervisionada, não a realização integral da visão conceitual.

## Segurança e dados

Não use o sistema para informações confidenciais reais sem antes configurar controles de acesso ao banco, backups e política de retenção. O SQLite armazena texto em claro. Os registros são isolados por usuário autenticado no nível das consultas. A análise estática do V99 não é uma auditoria de segurança de código. A aprovação V96 não dispara ações.
