# Ashley 1.0 — Motor de Conexão Humana e Autonomia Relacional

## Conteúdo
Este pacote preserva a estrutura do aplicativo e integra o novo motor ao `app/core/orquestrador.py`, à API `app/API/app.py` e ao `frontend/index.html`.

O motor está em `app/relationship/motor_conexao_humana.py`. Usa tabelas próprias no banco SQLite já configurado, sem alterar tabelas anteriores. A cada mensagem, a API acrescenta instruções de acolhimento, diálogo honesto, autonomia, avisos de risco e segurança ao prompt de chat. O orquestrador instancia o motor. A interface acrescenta consentimento opcional para acompanhamento e opção de exclusão.

## Instalação local
1. Faça backup completo da pasta atual, **incluindo o banco `data/` e seu `.env`**.
2. Descompacte este pacote em outra pasta, sem substituir sua instalação imediatamente.
3. Para atualização conservadora, copie somente os quatro arquivos de integração indicados abaixo, mantendo as pastas relativas:
   - `app/relationship/motor_conexao_humana.py` (novo)
   - `app/core/orquestrador.py` (alterado)
   - `app/API/app.py` (alterado)
   - `frontend/index.html` (alterado)
4. Reinicie: `py -m uvicorn app.API.app:app --reload --port 8000` na raiz do projeto.
5. Faça login, use Ctrl+F5 e teste uma conversa. O botão de acompanhamento está desativado por padrão.
6. Para testar a lógica sem API externa: `py -m unittest -v test_motor_conexao`.

## APIs novas (requerem autenticação)
- `GET /conexao/preferencias` — lê consentimento.
- `POST /conexao/preferencias` com `{ "acompanhar": true }` — autoriza lembrete genérico de bem-estar entre conversas (apenas adultos).
- `POST /conexao/limpar` com `{ "confirmar": true }` — apaga o acompanhamento.

## Privacidade e limites
- O acompanhamento é **desativado por padrão**. Quando autorizado, grava somente a categoria genérica `bem-estar`, nunca a mensagem íntima original, nesta nova tabela. A memória preexistente do aplicativo continua funcionando com suas próprias regras.
- A classificação de sofrimento/perigo usa **regras textuais simples**, não é diagnóstico e pode deixar passar sinais importantes ou gerar falsos positivos.
- Não há notificações autônomas, ações externas nem garantia de prevenção de crises.
- Menores não recebem acompanhamento persistente deste motor nesta versão. O chat usa as regras de faixa etária existentes.
- A voz neural e suas quotas não foram alteradas por este pacote.
- Os arquivos `.env`, bancos de dados, credenciais e históricos pessoais não estão incluídos no pacote.
- Os testes locais verificam a lógica do motor, mas **não substituem teste de integração real** com FastAPI, Gemini, login e navegador na máquina do usuário.
