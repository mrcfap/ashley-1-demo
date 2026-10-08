# Ashley 1.0 — pacote de homologação (não publicar ainda)

Este pacote consolida o protótipo de controle etário com o backend e a interface.

## Instalação local
1. Faça backup integral da instalação atual, principalmente `data/` e `.env`.
2. Extraia este pacote em outra pasta. Não substitua sua instalação em produção.
3. Crie `.env` a partir de `.env.example`, usando sua chave em ambiente seguro.
4. Instale `pip install -r requirements.txt` e execute `python -m uvicorn app.API.app:app --host 127.0.0.1 --port 8000`.
5. Valide `/health`, cadastro, login, sessão, logout, chat, visão, voz, imagem e vídeo com suas credenciais e cotas.

## Bloqueios de publicação
- O e-mail de responsável é autodeclarado, sem verificação de identidade e vínculo legal. `ASHLEY_ENV=production` bloqueia a aprovação parental até implementação adequada.
- O filtro etário do chat depende principalmente de instruções ao modelo; faltam moderação independente de entrada/saída, classificação multimodal e testes adversariais.
- Persistência de SQLite e arquivos gerados em hospedagem efêmera não está garantida; usar armazenamento persistente com backup.
- Acesso a arquivos gerados e outros endpoints deve ser auditado por isolamento entre usuários.
- O SDK, os modelos e as cotas Gemini precisam de testes reais com a conta de produção.
- É necessário testar segurança, concorrência, privacidade, retenção e recuperação antes de oferecer o produto a menores.

## Critérios para apresentação
É possível demonstrar o software em ambiente controlado, informando claramente quais recursos estão operacionais e quais ainda dependem de integração e validação.
