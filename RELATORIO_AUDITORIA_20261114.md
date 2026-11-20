# Axyntora / Ashley — auditoria local (14/11/2026)

## Escopo
Pacote recebido: Ashley Oficial final(20261114-142149).zip, 867 entradas, cerca de 63,9 MB descompactados. Auditoria estática e testes Python neste ambiente isolado; nenhuma implantação em Render/GitHub/Supabase, câmera, microfone, Ollama, credenciais ou serviços externos foi testada.

## Resultados reproduzíveis
- 283 arquivos `.py` analisados por `ast.parse`: 283 válidos, zero erros de sintaxe.
- Suíte geral: interrompida na coleta, 7 módulos com ImportError de `google.genai` ausente no ambiente. A dependência `google-genai>=3.2,<4` já consta de requirements.txt; a falha é de ambiente e não foi corrigida por substituição falsa.
- Suíte parcial, ignorando apenas os 7 módulos com erro de coleta: **259 testes aprovados, 1 falhou**. A falha restante (`test_identidade_http_respeita_persona_e_permissoes`) também depende do mesmo SDK ausente.
- Suíte direcionada (pragmática, privacidade da câmera, upload, agência, identidade e contexto): **27 aprovados, 1 falhou**, mesma dependência.
- Integração da pragmática já presente em `app/pragmatics/engine.py`; não foi substituída sem necessidade.

## Segurança e distribuição
O arquivo de origem contém arquivos `.env`, backups e bancos SQLite. A cópia de distribuição remove esses itens locais e caches compilados para não redistribuir credenciais, dados de usuários ou backups de autenticação. O original enviado pelo usuário não foi alterado. A remoção pode exigir recriar variáveis de ambiente e bancos no destino; **não substitua uma instalação em produção sem backup**. Revogue/rotacione credenciais que tenham sido compartilhadas.

## Pendências para homologação completa
1. Instalar dependências num ambiente virtual limpo (`python -m pip install -r requirements.txt`) e repetir `python -m pytest -q`.
2. Testar integração real com Ollama, Gemini, TTS, câmera e interfaces, inclusive consentimento de visitantes e autorização.
3. Validar banco Supabase/Postgres, autenticação, migrações, persistência e backup/restauração com dados de teste.
4. Testar endpoints HTTP, desempenho, cargas, reconexão e implantação em staging na Render.
5. Fazer revisão de segurança, segredos, dependências e privacidade antes de produção.

**Status: HOMOLOGAÇÃO PARCIAL.** Não há base para declarar 100% aprovado.
