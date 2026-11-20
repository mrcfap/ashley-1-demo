# Axyntora — ciclo 1 de integração e homologação

Base: Axyntora_ELO_HORIZONTE_VIVO_ESSENTIA_20261030.zip.

## Alterações realizadas
- Conexão consultiva de ELO, HORIZONTE VIVO e ESSENTIA ao `OrquestradorAshley` pelo método `avaliar_fundacao_humana`.
- Conexão consultiva de PARALLAX pelo método `avaliar_decisao_supervisionada`.
- Exportação de `HumanCharter` no pacote `human_foundation`.
- Remoção de cópia comprovadamente inválida `app/memory/memoria_longa_com_erro.py`; o arquivo funcional `memoria_longa.py` foi preservado.
- Novos testes de integração por extração AST dos métodos reais, permitindo validar a lógica sem inicializar fornecedores externos.

## Evidências
- `python -m compileall -q app tests`: APROVADO.
- `python -m unittest discover -s tests -p test_integration_human_supervision.py -v`: 3/3 APROVADOS.
- `python -m unittest discover -s tests -p test_human_foundation.py -v`: 9/9 APROVADOS.
- Suíte geral `python -m unittest discover -s tests -p 'test_*.py' -q`: 102 testes descobertos, 6 erros por dependência ausente `ddgs` ao importar o orquestrador. Não homologada integralmente.

## Escopo e limites
- Os novos pontos de entrada são internos e consultivos, não são endpoints HTTP e não executam ações externas.
- A identidade precisa ser validada pelo chamador autenticado antes de usar `avaliar_fundacao_humana`.
- Não houve homologação end-to-end de API, banco de dados, Gemini/Ollama, vídeo, voz, serviços externos ou produção.
- Os demais agentes continuam exigindo integração controlada; não é correto declarar 100% homologado.
