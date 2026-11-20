# Atualização da conversa Ashley e Ashen

No Windows, pare o Uvicorn com Ctrl+C. Extraia a pasta do ZIP e copie o
conteúdo de `Ashley Oficial final` para a instalação existente, aceitando a
substituição dos arquivos de código. Mantenha na instalação seus arquivos
`.env` e `data`, que guardam configuração, contas e memória. O pacote omite
bancos, backups e mídia gerada da instalação original.

No PowerShell, na pasta da instalação, inicie a API.

```powershell
python -m uvicorn app.API.app:app --reload
```

Abra http://127.0.0.1:8000/ e recarregue a página.

## Teste na interface

1. No modo dual, envie **boa tarde**. Ashley e Ashen devem cumprimentar você.
2. Envie **fale algo sobre o futuro da IA**. Cada um deve desenvolver uma ideia.
3. Para quatro perspectivas, envie **Comitê: compare duas maneiras de lançar um piloto da Axyntora**.
4. Envie **Guarde o fato fornecedor: Aurora** e, no chat individual, envie
   **Corrija o fato fornecedor: Horizonte**. Em uma nova conversa, envie
   **Qual é o fato fornecedor?**. O valor que deve aparecer é **Horizonte**.
   A consulta também funciona após reiniciar o servidor com a mesma conta.

A consolidação dos fatos explícitos roda na inicialização e a cada 24 horas
de execução. A interface aberta com uma conta conectada verifica a API a
cada 15 segundos e exibe um aviso após três falhas consecutivas. O sinal de
qualidade do chat dual alimenta as propostas do painel administrativo V11,
conforme a política da conta. As propostas seguem o fluxo de revisão existente.
