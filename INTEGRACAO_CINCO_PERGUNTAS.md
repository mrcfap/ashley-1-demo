# Identidade Evolutiva — cinco perguntas

A camada `app/core/identidade_evolutiva.py` fornece identidade operacional, origem, missão, capacidades e direção. O chat injeta esse contexto no prompt da persona, permitindo respostas contextualizadas em vez de um questionário fixo. `propor_reflexao` armazena lacunas e objetivos para revisão humana; não reescreve código nem altera políticas. O inventário de rotas indica presença, não homologação.

## Testar

`python -m pytest tests/test_identidade_evolutiva.py -q`

Execute também a suíte geral e testes manuais autenticados de `/chat` antes de implantar no Render. O arquivo `.env` original e bancos privados foram intencionalmente excluídos do pacote de distribuição: preserve suas configurações locais com segurança. Não substitua um banco existente por um vazio.
