# Ashley 1.0 — Extensão V53 a V56 (protótipo isolado)

O pacote preserva os arquivos de código existentes do ZIP de entrada e acrescenta `app/future_v53_v56/engines.py`.

- **V53 PROMETHEUS**: comparação determinística de cenários fornecidos; não faz previsão factual.
- **V54 CONDUCTOR**: plano de delegação de especialistas; não executa agentes.
- **V55 GUARDIAN**: política de contingência; reexecução só sugerida quando a tarefa é idempotente.
- **V56 HORIZON**: registro persistente de lacunas, hipóteses, plano de testes, evidências e aprovação humana; não escreve ou executa código automaticamente.

## Testar
Na raiz do projeto: `python TESTE_V53_V56.py`.

## Integração pendente
Não conectado ao `app.py`, ao orquestrador, ao login ou ao V52 SYNAPSE. `authorized=True` é apenas uma flag de protótipo, **não é autenticação**. Em produção, substituir por autorização verificada no servidor, isolar os dados por usuário, adicionar migrações, observabilidade, testes ponta a ponta, sandbox real e limites de recursos.

**Não substituir a instalação em produção por este ZIP.** Faça backup e integre incrementalmente.
