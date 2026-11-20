# Axyntora V85–V94 — pacote incremental supervisionado

**Base:** Ashley Oficial final(20261018-160437).zip. Instalar na raiz do projeto, mantendo a estrutura `app/`.

## Instalação
1. Pare Uvicorn (Ctrl+C) e faça backup da pasta inteira.
2. Extraia o ZIP na raiz `Ashley Oficial final`, aceitando substituir **somente** `app/API/app.py` e `app/nextgen/symphony_bridge.py`.
3. Inicie `python -m uvicorn app.API.app:app --reload`.
4. Abra `/docs`, autentique usando o fluxo normal da aplicação e verifique `GET /api/v1/engines/nextgen/catalog`.
5. Teste `POST /api/v1/engines/nextgen/86/run` com `{"action":"simulate","data":{"scenarios":[{"name":"A","probability":0.5,"impact":10}]}}`.
6. Teste `POST /api/v1/engines/v84/plan` e confirme `nextgen_capability_catalog` na resposta.
7. Execute `python -m pytest tests/test_v85_v94.py -q`.

## Contratos implementados
`GET /api/v1/engines/nextgen/catalog`
`GET /api/v1/engines/nextgen/{engine}/status`
`POST /api/v1/engines/nextgen/{engine}/run`

Ações por motor: V85 consolidate/status; V86 simulate; V87 propose; V88 commit/observe/status; V89 investigate; V90 budget; V91 assess; V92 modulate; V93 partition; V94 compose.

## Limites reais
Protótipos funcionais limitados: V85 memória volátil (não altera pesos); V86 cenários numéricos fornecidos pelo usuário (não JEPA); V87 só propõe, sem gerar/executar código; V88 observações manuais voláteis; V89 planejamento de pesquisa sem navegar; V90 orçamento estimado, sem medidor de energia; V91 classificação de campos, sem criptografia homomórfica/zk; V92 tom consentido, sem diagnóstico emocional; V93 agentes lógicos planejados, sem paralelismo P2P; V94 composição de plano, sem execução. Não afirmar que estas capacidades avançadas estão implementadas.

**Integração:** router registrado em FastAPI e catálogo V85–V94 incluído no resultado do V84 SYMPHONY, sem alterar o seletor do orquestrador central, a autenticação, a voz, a câmera ou o banco de usuários. **Não há execução autônoma.**

**Segurança:** use token autenticado normal, nunca compartilhe tokens. Estado V85/V88 fica em RAM e é perdido ao reiniciar; não é adequado para dados sensíveis. A integração em `/chat` e o despacho de tarefas reais exigem testes adicionais.
