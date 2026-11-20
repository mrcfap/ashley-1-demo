# Ashley — Agentes Autônomos Fase 3 (incremental)

## Instalação
1. Faça backup e desligue o Uvicorn.
2. Extraia este ZIP na pasta `Ashley Oficial final`, mesclando a pasta `app` e `tests`.
3. No PowerShell, na raiz do projeto, rode:
   `python -m unittest discover -s tests -p "test_phase3.py" -v`
4. Confira também os testes da Fase 2.

## Uso em Python
`from app.agents.autonomous.phase3 import AutonomousCodingPhase3`
`agent = AutonomousCodingPhase3(".")`
`resultado = await agent.propose_and_review("Melhore os comentários", ["app/algum_modulo.py"])`

A chamada com Gemini consome cota e pode falhar por indisponibilidade.

## Limites
Esta etapa usa o Gemini da Fase 2 para produzir código e adiciona revisão AST local, sem executar código gerado. Não implementa ainda agentes LLM independentes, testes isolados, API de painel nem integração efetiva com V22. Nenhuma alteração é promovida automaticamente. Revisão AST não garante segurança.
