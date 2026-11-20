# Ashley 1.0 — Implementação incremental V77–V80

## Entrega
- V77 WITNESS: API autenticada de registro de evidências fornecidas pelo usuário e métricas agregadas.
- V78 COVENANT: criação/listagem de organizações do próprio usuário, consentimento por escopo e exclusão dos dados locais deste módulo.
- V79 OMNIA: preparação de preferência de idioma. **Não** detecta nem traduz idiomas, nem implementa STT/TTS.
- V80 AETERNA: revisão determinística de missões com referências a evidências do mesmo usuário. **Não** executa missões autonomamente.

## Endpoints
GET /api/v1/engines/v77-v80/status
POST /api/v1/engines/v77/evidence
GET /api/v1/engines/v77/metrics
POST /api/v1/engines/v78/organizations
GET /api/v1/engines/v78/organizations
POST /api/v1/engines/v78/organizations/{org}/consent
DELETE /api/v1/engines/v78/my-data
POST /api/v1/engines/v79/language/prepare
POST /api/v1/engines/v80/mission/review

Todas exigem Bearer token válido via identidade do backend existente.

## Instalação
1. Faça backup integral da sua instalação original (inclusive dados, .env e banco) em local privado.
2. Esta entrega é uma cópia do código, sem .env, bancos, uploads, mídias ou logs privados. Não substitua seu diretório de dados.
3. Copie o código para um ambiente de testes e mantenha seu .env e banco locais protegidos.
4. Inicie pelo comando que você já usa para a Ashley e confira /docs.
5. Valide login, operações dos novos endpoints e regressão das rotas antigas antes de qualquer produção.

## Limitações / segurança
- Sem testes end-to-end contra banco real e serviços externos.
- Consentimento do V78 não cancela tarefas existentes em outros módulos.
- Exclusão afeta apenas o banco v77_v80.db, não sistemas externos ou outros bancos.
- Isolamento de organizações limitado às rotas novas; ainda não é multi-tenant completo.
- Dados de evidência são declarações do usuário, não provas independentes.
- Para produção: isolamento transversal, autenticação/autorização por organização, migrações, criptografia, rate limiting, auditoria, testes de carga, proteção etária e revisão LGPD.
