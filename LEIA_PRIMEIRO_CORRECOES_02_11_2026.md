# Axyntora — Correções de 02/11/2026

## Alterações realizadas
- Rota autenticada POST `/api/v1/triad/micd/converse` agora aceita `session_id` opcional e retorna o identificador da sessão.
- O histórico da conversa fica em memória durante a execução do servidor, isolado por usuário e sessão (até 100 sessões; 12 mensagens por sessão).
- Controle de concorrência evita duas solicitações simultâneas na mesma sessão (HTTP 409).
- DELETE `/api/v1/triad/micd/converse/{session_id}` limpa a sessão autenticada.
- Validação do histórico fornecido pela interface e tratamento de indisponibilidade do Ollama.
- Testes automatizados adicionados em `tests/test_triad_dual_sessions.py`.

## Instalação no Windows
1. Faça backup da pasta atual.
2. Extraia este ZIP em uma pasta NOVA. Não sobrescreva seu `.env` original.
3. Copie o seu `.env` local para a nova pasta, sem compartilhar credenciais.
4. No ambiente Python com as dependências instaladas, rode `python -m pytest -q tests/test_triad_dual_sessions.py`.
5. Inicie a API como anteriormente: `uvicorn app.API.app:app --reload`.
6. Verifique autenticação e Ollama local antes de testar a rota dual.

## Limites e pendências
- A memória de sessão é VOLÁTIL, não persiste após reinício e não é compartilhada entre workers.
- O modo dual continua usando o Ollama local; voz, câmera, persistência de longo prazo e integração com a interface principal NÃO foram homologadas nesta entrega.
- O teste completo `python -m pytest -q tests` não chegou a executar toda a suíte: a coleta encontrou dependência ausente `google.genai` neste ambiente. Isso não demonstra defeito nos testes afetados.
- Os testes de diálogo usam um modelo simulado (mock); é obrigatório testar com Ollama real no Windows.
- O arquivo `.env` com segredos foi intencionalmente EXCLUÍDO do ZIP.
