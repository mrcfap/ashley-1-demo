# Auditoria geral técnica — Axyntora / Ashley 1.0

**Data:** 02/11/2026  
**Base examinada:** `Ashley Oficial final(20261102-182423).zip`  
**Resultado:** correções aplicadas em cópia de trabalho; homologação parcial com evidências reproduzíveis.  
**Importante:** o ZIP original não foi alterado.

## 1. Escopo e inventário

- 784 entradas no arquivo ZIP original.
- 171 arquivos Python em `app/` após retirar da área ativa uma cópia legada truncada.
- 49 arquivos de teste em `tests/`.
- 263 arquivos Python no projeto e testes examinados.
- 52 pacotes/módulos de primeiro nível identificados.
- 230 classes e 1.008 funções/métodos encontrados por AST em `app/`.
- 58 handlers HTTP diretos declarados na API principal e 149 rotas registradas após inclusão dos routers.
- Nenhum import local `app.*` não resolvido foi encontrado na análise estática.

O inventário completo de pacotes, módulos, classes e situação de auditoria está em `INVENTARIO_MOTORES_AGENTES_INTEGRACOES.csv`.

## 2. Correções aplicadas

### 2.1 V22 — Motor de Execução Persistente

Arquivo: `app/tasks/motor_execucao_v22.py`

- `recuperar_interrompidas()` agora respeita `tentativas >= max_tentativas`, encerrando como `FALHOU` quando o limite foi consumido.
- Recuperação deixou de ocorrer automaticamente a cada construção de instância. Pode ser solicitada no bootstrap controlado por `recuperar_ao_iniciar=True` ou pelo método `CodingV22Bridge.recover_after_restart()`.
- `aprovar()` só aceita tarefas em `AGUARDANDO_APROVACAO`.
- `concluir()` só conclui tarefa em `EXECUTANDO`, com atualização condicional no banco.
- `falhar()` só altera tarefas ainda em `EXECUTANDO`; não reativa tarefas canceladas.
- A reserva geral de `proxima()` preserva a transação `BEGIN IMMEDIATE`.

**Atenção operacional:** a recuperação deve ser chamada uma única vez pelo bootstrap do worker que realmente controla a fila. Não se deve chamar em cada requisição. O pacote ainda não tem um worker/consumidor geral V22 ligado ao startup da API.

### 2.2 Fase 4 / Fase 5

Arquivos: `app/agents/autonomous/phase4.py`, `phase5.py`

- A Fase 4 verifica o limite de tentativas na própria operação atômica de reserva.
- A tarefa é revalidada antes da conclusão; cancelamento ocorrido durante a geração não é convertido em conclusão.
- A importação da Fase 3/Gemini passou a ser tardia, evitando exigir o SDK Gemini só para instanciar a fila.
- Aprovação da geração continua separada da autorização de publicação.
- A Fase 5 continua sendo planejamento governado; testes automáticos e publicação em produção permanecem desativados por padrão.

### 2.3 Self-Coding V9/V10

Arquivo: `app/evolution/self_coding_engine.py`

- Validação de workspace por caminho resolvido e marcador `.ashley_workspace.json`.
- Remoção de comparação de caminho baseada em `startswith` e uso de `Path.is_relative_to`.
- Restrições de edição/diff/promoção automática a arquivos Python.
- Identificadores de proposta validados antes da criação do workspace.
- Exclusão de `.env*`, bancos, WAL/SHM, perfis biométricos, logs, backups e missões locais ao copiar workspace.
- Test runner aceita apenas o interpretador Python configurado, rejeita `-c` e exige scripts dentro do workspace.
- Ambiente do subprocesso é filtrado; variáveis de credenciais do servidor não são herdadas.
- Rollback valida destino e ignora links simbólicos.

**Limite importante:** o executor ainda é um subprocesso Python no mesmo sistema operacional e com as permissões do usuário do servidor. Não é uma sandbox de SO/container: código candidato ainda poderia tentar acessar arquivos externos ou rede. Não liberar execução de código não confiável em ambiente comercial sem isolamento adicional.

### 2.4 Autenticação, autorização e isolamento de dados

Arquivos: `app/API/app.py`, `app/security/auth.py`, `app/security/commercial_guard.py`, `app/security/postgres.py`

- Migração SQLite agora cria `is_admin` com padrão falso.
- Primeira conta criada por `auth.create()` recebe `is_admin=TRUE`; contas comuns permanecem não administrativas.
- Tratamento de duplicidade não importa `psycopg` dinamicamente dentro de uma tupla de exceção SQLite.
- `/auth/register-first` exige `ASHLEY_BOOTSTRAP_TOKEN` no header `X-Ashley-Bootstrap-Token`.
- Rotas com `user_id` no caminho verificam propriedade da sessão; administrador pode atravessar escopo conforme política administrativa.
- `/memoria/guardar` deriva a identidade do token, em vez de usar `user_id=1` como padrão.
- Upload de arquivo e geração de documentos derivam o usuário autenticado e validam qualquer `user_id` opcional.
- Campos JSON `user_id` pertinentes deixaram de assumir silenciosamente a conta 1.
- Arquivos de imagem/vídeo gerados passaram a ser armazenados em diretório por usuário; o download exige o mesmo `user_id` autenticado.
- CORS passou a aceitar GET, POST, PUT, PATCH, DELETE e OPTIONS.

**Compatibilidade:** clientes que enviam JSON para modelos com `user_id` precisam continuar enviando o identificador autenticado. URLs de arquivos gerados devem usar a URL retornada pela API (`/gerados/{user_id}/{nome}`).

### 2.5 Visão, câmera e privacidade

Arquivos: `app/API/app.py`, `app/vision/camera.py`

- `/vision/capture` passou a fazer detecção local de rostos, não comparação biométrica contra perfis.
- Identidade biométrica fica `None` e é explicitamente marcada como desativada até existir fluxo de consentimento adequado.
- Análise multimodal externa só é solicitada quando `consentimento_analise_multimodal=true`; o padrão é falso.
- Captura temporária é removida ao final do processamento, inclusive em erro; a API não retorna caminho persistente da imagem.
- A câmera lógica é desativada ao final da captura.
- Entrada Base64 tem limite, validação estrita e checagem de assinatura JPEG/PNG/WebP.
- As rotas de presença continuam fazendo detecção sem identificação nem retenção de quadros.

**Compatibilidade:** o frontend deve enviar `consentimento_analise_multimodal=true` somente quando a análise externa estiver autorizada. Sem isso, a API retorna estado aguardando consentimento e mantém apenas a detecção local.

### 2.6 Arquivo legado

`app/memory/memoria_longa_com_erro.py` era uma cópia truncada, com erro sintático, e não tinha referências de importação. Foi removida da área ativa. O conteúdo idêntico permanece preservado como texto em `backup_legado/memoria_longa_com_erro.py.txt`.

## 3. Evidências de testes

### 3.1 Sintaxe

- `py_compile` em todos os 263 arquivos Python: **263 aprovados, 0 erros**.

### 3.2 Suíte automatizada parcial

Com cinco arquivos de teste temporariamente excluídos por falta do SDK `google-genai` no ambiente de auditoria:

```text
228 passed in 3.87s
```

Arquivos excluídos desta execução:
- `tests/test_phase2.py`
- `tests/test_phase3.py`
- `tests/test_v77_v80_auditoria.py`
- `tests/test_v84_http.py`
- `tests/test_v84_registry.py`

### 3.3 Suíte completa

A execução sem exclusões não terminou a coleta: **5 erros de importação**, todos decorrentes de `ImportError: cannot import name 'genai' from 'google'`. `google-genai` está declarado em `requirements.txt`, mas não estava instalado no ambiente de auditoria.

O ambiente de auditoria também não tinha `ddgs`, `edge_tts` e `psycopg`; essas dependências estão declaradas no `requirements.txt`. Não foi feita instalação de pacotes nem conexão a serviços externos.

### 3.4 Testes HTTP de fumaça com dependências simuladas

Com SDK Gemini simulado e autenticação de teste, foram verificados:
- Rotas de diagnóstico, casos e visão com ID de outro usuário: HTTP 403.
- Status/encerramento de presença de outro usuário: HTTP 403.
- Download de arquivo gerado por outra conta: HTTP 403; proprietário: HTTP 200.
- Gravação de memória para outro usuário: HTTP 403; mesma conta: HTTP 200.
- `/chat` sem `user_id`: HTTP 422, sem cair silenciosamente na conta 1.
- Bootstrap administrativo sem token: HTTP 403; com token correto: HTTP 200.
- `/vision/capture`: não chamou reconhecimento biométrico, não chamou análise multimodal sem consentimento e retornou `retida=false`.

Esses são testes de rota com mocks; não são homologação de Gemini, câmera física ou provedores reais.

## 4. Mapa de integração dos motores e agentes

### Núcleo e motores com integração identificada

- `app/core/orquestrador.py`: conecta V26, V31–V35, V44–V47, V77–V80, memória estratégica, relacionamento, casos, autoevolução V9–V11, continuidade V12–V21 e Cognitive Hub.
- API principal registra routers V62–V65, V66–V75, V76, V77–V80, V81–V84, V84 Plan, Triad, V85–V94 e V95–V100.
- Rotas diretas incluem autenticação, chat, memória, arquivos, documentos, imagem, vídeo, TTS, evolução e visão.

### Componentes presentes, porém com integração parcial ou limitada

- **V22:** motor de fila persistente e ponte Fase 4/5 existem, mas não há consumidor geral nem rota de API que execute continuamente a fila. A integração V22 com o orquestrador ainda precisa ser construída.
- **Fases 2–3:** geração de proposta e revisão estática. O código declara que os papéis não são modelos/agentes independentes e que os testes de código não confiável não são executados nessa fase.
- **Fase 5:** plano governado; não habilita testes automáticos ou publicação.
- **V27–V30:** há motores e status; V28 depende de endpoint externo configurado. Não foi encontrada rota de geração musical na API principal.
- **V23–V26:** integração parcial; o próprio endpoint de status informa que análise acústica/facial automática não está implementada.
- **V81–V84:** componentes defensivos e roteamento declarativo; não são executor de ferramentas externas.
- **V85–V94 e V95–V100:** routers registrados e testes disponíveis; o núcleo V95–V100 se declara protótipo funcional limitado, sem LLM, ferramentas externas, deploy ou execução autônoma.
- **V76 e V77–V80:** routers registrados; testes de humanidade, evidências, organizações, consentimento e idioma existem.

### Agentes e integrações

- `app/agents`: 16 arquivos e 32 classes top-level. Há coordenador, fases de programação e agentes especializados; alguns papéis ainda são descrições/contratos, não agentes independentes executando em paralelo.
- `app/integrations`: 6 arquivos e 21 classes top-level. A governança MCP é fail-closed, mas não executa ferramentas.
- `app/governance/decision_ledger.py`: ledger experimental com hash encadeado; não é imutável contra administrador, não tem assinatura criptográfica e documenta que precisa de lock para concorrência.
- `app/integrations/mcp_governance/policy.py`: escrita/sensível fica aguardando autorização; `approved_action_id` ainda não é validado/consumido por um adaptador V22.
- `app/vision`: detecção e presença estão separadas da identificação. O módulo biométrico local continua no código, mas a rota de captura não o chama.

## 5. Pendências antes de homologação comercial

1. Instalar todas as dependências do `requirements.txt` no Windows e executar `python -m pytest -q tests` sem exclusões.
2. Criar worker/consumidor V22 e integrá-lo ao startup controlado, com lease/heartbeat se houver múltiplos workers.
3. Implementar sandbox real de sistema operacional/container para código candidato.
4. Vincular aprovação administrativa a usuário, tarefa, arquivos/hash, expiração e consumo único; não usar apenas booleano `autorizado=True`.
5. Integrar V22, V9/V10, V11, Ashen e ledger com contratos e testes de ponta a ponta.
6. Implementar fluxo de consentimento do visitante para pesquisa pública e qualquer identificação; a pesquisa pública não está implementada nesta entrega.
7. Conectar evento `convite_conversa` da presença ao fluxo de voz/TTS; hoje o módulo de presença retorna eventos, mas não inicia sozinho a conversa por voz.
8. Testar Gemini, Ollama, TTS, geração de imagem/vídeo, música e câmera física com credenciais e hardware reais.
9. Adicionar rate limiting e monitoramento de tentativas de login/recuperação de senha.
10. Avaliar lock/assinatura e retenção do Decision Ledger antes de usá-lo como auditoria de produção.

## 6. Instalação segura da cópia revisada

1. Pare o servidor atual e faça backup integral da pasta local.
2. Extraia este pacote em uma pasta nova.
3. Copie manualmente o `.env` original para a pasta nova. **Não use `.env.backup-antes-sqlite` como configuração.**
4. Copie os bancos locais e dados que precisam ser preservados da pasta antiga (`data/*.db`, `data/*.sqlite3`, `app/vision/perfis_faciais`, se existirem). Esses dados foram excluídos do pacote de distribuição para proteger contas, memórias e biometria.
5. Confira `ASHLEY_BOOTSTRAP_TOKEN` no `.env` se for uma instalação nova. Em uma instalação já cadastrada, não recrie a primeira conta.
6. Instale dependências: `python -m pip install -r requirements.txt`.
7. Execute `python -m pytest -q tests`.
8. Só então inicie a API e valide os serviços externos.

**Conclusão:** a cópia recebeu correções relevantes e passou em 228 testes disponíveis e em compilação integral. A homologação geral permanece **parcial**, não 100%. Hardware, serviços externos, worker V22, sandbox de sistema operacional e fluxos completos de autonomia ainda precisam de validação.
