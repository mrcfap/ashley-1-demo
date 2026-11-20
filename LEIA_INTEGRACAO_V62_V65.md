# Ashley V62-V65 — Integração incremental de API

## Instalação
1. Faça backup da pasta `Ashley Oficial final` e pare o Uvicorn.
2. Extraia este ZIP **na raiz** da pasta `Ashley Oficial final`, mantendo as pastas `app/` e `tests/`.
3. Execute `python INSTALAR_INTEGRACAO_V62_V65.py`. O instalador faz cópia de segurança de `app/API/app.py` e acrescenta **somente** o registro do router; é idempotente.
4. Execute `python -m unittest discover -s tests -p "test_v62_v65_integration.py" -v`.
5. Inicie a aplicação normalmente e consulte `/docs` com a sessão de autenticação apropriada para experimentar as rotas.

## Rotas
- `POST /api/v1/engines/v62/projects` — projeto social
- `GET /api/v1/engines/v62/projects` e `GET /api/v1/engines/v62/projects/{id}`
- `POST /api/v1/engines/v62/projects/{id}/steps/{step_id}/evidence`
- `POST /api/v1/engines/v62/projects/{id}/steps/{step_id}/confirm`
- `POST /api/v1/engines/v63/suggest` — sugestão voluntária sem diagnóstico
- `POST /api/v1/engines/v64/outcomes` e `GET /api/v1/engines/v64/outcomes/{id}`
- `POST /api/v1/engines/v64/outcomes/{id}/evidence` e `/confirm`
- `POST /api/v1/engines/v65/assess` — rótulos conservadores de evidência

Todas exigem `Authorization: Bearer <token Ashley>`. O ID do usuário é obtido da autenticação, nunca do JSON. Contas menores de idade ficam bloqueadas nestas rotas até existir proteção específica.

## Limites reais
- V62 usa SQLite em `data/v62_nexus.db`; V64 usa `data/v64_outcomes.db`.
- Confirmação humana indica declaração do proprietário, **não** verificação independente.
- V65 não aceita que um cliente se autodeclare verificador independente.
- V63 não realiza diagnóstico, classificação de empregados nem ação externa.
- **Não integra ainda** os fluxos de conversa, interface, memória de longo prazo, fila V22 ou ações MCP. Nenhum desses pontos é declarado como concluído.
- Testes executados em ambiente isolado com autenticação simulada: não substituem testes end-to-end da aplicação real no Windows.

## Reversão
Pare o servidor, restaure o backup `app_backup_antes_v62_v65_*.py` para `app/API/app.py` e reinicie. Os novos bancos ficam separados dos dados anteriores.
