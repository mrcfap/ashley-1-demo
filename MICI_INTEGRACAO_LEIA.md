# MICI — componente transversal de imparcialidade

Integração no `app/core/orquestrador.py`, na composição do contexto do modelo. Não foi criado um novo motor: a contagem planejada permanece V1–V84. O MICI reforça as diretrizes de coerência (V23), integração (V26), proteção (V83) e orquestração (V84), sem alegar que estes motores tenham sido homologados.

A política é enviada ao contexto do modelo, não é um filtro determinístico de saída. `verificar_heuristicas` fornece somente sinais para revisão humana. Os três pares de perguntas em `PARES_TESTE` são casos de avaliação comparativa, não um teste automatizado de equivalência semântica das respostas. Para homologação, executar os testes, avaliar respostas reais do provedor com revisão humana e verificar se outros fluxos de chat também usam `montar_contexto_para_modelo`.

Não foram alterados segredos, bancos de dados ou arquivos de usuário. Recomenda-se executar inicialmente em cópia de teste.
