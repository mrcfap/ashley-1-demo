# Ashley 1.0 — Atualização supervisionada V81–V84 (16/10/2026)

## O que foi alterado
- app/nextgen/api.py: 11 rotas novas com autenticação por sessão da Ashley.
- app/API/app.py: registra as rotas; pré-triagem de mensagens, prompts de imagem/vídeo e uploads.
- Uploads passam por validação preliminar de nome, assinatura executável e limite de 25 MB.
- Nenhum motor antigo foi removido, nem o orquestrador foi substituído.

## Limites IMPORTANTES
- V81 trabalha com eventos visuais, NÃO com streaming real, WebSocket ou sincronização VAD.
- V82 apenas propõe ações, NÃO executa nem persiste aprovações.
- V83 NÃO é antivírus; não garante detectar malware, conteúdo ilícito ou ataques. Use antivírus, quarentena e varredura em produção. A triagem textual é limitada e pode errar.
- V84 é uma porta de decisão, NÃO é ainda a orquestração completa.
- Avatar original preservado; não foi implantada animação facial realista 3D/lip-sync.
- Geração de imagem/vídeo/música depende de provedores e de testes no computador do usuário. Nenhum teste externo foi realizado.
- Testes das cinco fases autônomas não foram homologados.

## Instalação segura
1. Pare o Uvicorn (Ctrl+C).
2. Faça backup COMPLETO da pasta atual, incluindo .env e data/.
3. Copie os arquivos deste pacote sobre o código atual, sem apagar .env, data/ ou os dados locais.
4. Inicie: python -m uvicorn app.API.app:app --reload --host 127.0.0.1 --port 8000
5. Faça login na interface; execute as consultas de status com o token da sessão autenticada (não compartilhe o token).
6. Consulte /docs autenticado; GET /api/v1/engines/v81/status a v84/status.
7. Se houver erro, restaure o backup. Não exponha a porta 8000 na internet antes de auditoria.

## Testes locais executados
- python -m compileall app/nextgen app/API/app.py
- python -m unittest discover -s tests -p test_nextgen.py (4 testes OK)
- Importação isolada do roteador (11 rotas OK)

## Dados pessoais e credenciais
O pacote NÃO contém o arquivo .env, banco de dados, uploads, arquivos gerados ou ambientes de evolução, para evitar exposição acidental e sobrescrita de dados. Conserve-os da instalação existente.
