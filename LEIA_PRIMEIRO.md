# Correção incremental V84 SYMPHONY ↔ V85–V94

Base: arquivos originais do ZIP `Ashley Oficial final(20261018-160437).zip` e `symphony_bridge.py` do pacote V85–V94 instalado anteriormente.

## Instalação (Windows)
1. Pare o Uvicorn (`Ctrl+C`) e faça backup da pasta do projeto.
2. Extraia este ZIP **na raiz** `Ashley Oficial final`, preservando a estrutura `app/nextgen/...`, e confirme a substituição dos dois arquivos `symphony_http.py` e `symphony_bridge.py`.
3. Execute `python -m pytest tests/test_v85_v94.py tests/test_v84_v94_bridge.py -q`.
4. Inicie `python -m uvicorn app.API.app:app --reload`.
5. Com login ativo, abra `/api/v1/engines/v84/integration-catalog` no console via `fetch`, e confira `inventory.range` = `V1-V94` e 94 entradas.
6. Teste `POST /api/v1/engines/v84/plan` com `{"objective":"Investigar evidências e proteger privacidade de dados pessoais","complexity":"media"}`. A resposta deve conter `nextgen_selected_engines` incluindo V89 e V91.

## Limites reais
- Catálogo V1–V84 continua sendo inventário estático; referências não provam execução.
- V85–V94 vêm do registro explícito do pacote anterior; são protótipos limitados, não motores plenamente homologados.
- Seleção do V84 é heurística por palavras-chave, com justificativa `matched_terms`; não é decisão semântica de LLM.
- **Nenhum motor é executado pelo planejamento**. `execution_authorized` permanece `false`; nenhuma ação externa ou escrita em produção é liberada.
- `/chat` e o orquestrador principal ainda não recebem despacho automático dos motores novos.
- O erro de sintaxe em `app/memory/memoria_longa_com_erro.py` não é alterado por este pacote.
