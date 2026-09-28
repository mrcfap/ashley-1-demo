ASHLEY 1.0 — BACKEND MULTIMODAL CONSOLIDADO

ARQUIVOS DESTE PACOTE
1. app/API/app.py
2. app/services/gemini_service.py
3. app/memory/memoria_longa.py
4. .env.example
5. requirements_multimodal.txt

IMPORTANTE
Este pacote COMPLEMENTA o projeto existente. Ele depende dos módulos já existentes:
- app/core/orquestrador.py
- app/tools/ferramentas.py
- app/relationship/memoria_relacional.py
- app/memory/memoria_estrategica.py
- app/evolution/reflexao.py
- app/agents/planner.py
- app/agents/critic.py

NÃO apague esses módulos.

INSTALAÇÃO
Na raiz "Ashley oficial":
  py -m pip install -r requirements_multimodal.txt

Copie app/API/app.py para app/API/app.py
Copie app/services/gemini_service.py para app/services/gemini_service.py
Copie app/memory/memoria_longa.py para app/memory/memoria_longa.py

Se as pastas app/services não existirem, crie-as.
Mantenha seu .env atual e acrescente as variáveis do .env.example sem apagar sua chave.

EXECUÇÃO
  py -m uvicorn app.API.app:app --reload

TESTES
  http://127.0.0.1:8000/docs
  GET  /health
  GET  /diagnostico/usuario/1
  POST /web/pesquisar
  POST /chat
  POST /arquivo/analisar
  POST /imagem/gerar
  POST /video/gerar
  POST /memoria/guardar
  GET  /memoria/buscar/1
  GET  /gerados/{nome}

MEMÓRIA
- SQLite persistente no data/ashley.db.
- Memórias explícitas separadas por user_id.
- Histórico de interações persistente.
- O contexto relevante é injetado no chat.
- Esta versão usa busca lexical simples e ordenação por importância/permanência.
- Evolução futura recomendada: embeddings/vetores + PostgreSQL/pgvector quando houver escala.

VÍDEO
- A geração pode demorar vários minutos.
- Disponibilidade, cobrança, quotas e modelos dependem da conta/provedor.
- O endpoint aguarda a operação até VIDEO_TIMEOUT_SECONDS.

SEGURANÇA
- user_id deve ser > 0.
- nomes de arquivos são saneados.
- uploads têm limite configurável.
- uploads temporários são removidos por padrão.
- arquivos gerados ficam em data/generated.
