# Oito agentes de aprimoramento — protótipos isolados

Os oito componentes são classes Python testáveis em `app/agents/enhancement/agents.py`.
Não foram conectados automaticamente à API nem ao orquestrador para evitar regressões.

| Agente | Implementado neste pacote | Limite atual |
|---|---|---|
| MNEMOSYNE | Memória consentida em RAM, revisão e exclusão | Sem persistência ou busca semântica |
| ATLAS | Estados de missões e autorização | Não executa tarefas |
| SPECTRA | Linha do tempo multimodal por referências | Não interpreta áudio/imagens |
| DARWIN | Gate de verificações e aprovação | Não executa testes nem deploy |
| IMPACT | Comparação numérica com evidência | Não infere causalidade |
| ORACLE | Cenários determinísticos | Não é previsor treinado |
| IMMUNIS | Política de permissão local | Não substitui autenticação/RBAC |
| METACORE | Avaliação de indicadores | Não altera modelos automaticamente |

Teste: na raiz da pasta, execute `python -m unittest discover -s tests -p test_enhancement_agents.py -v`.

Próximos passos para integração: contrato de API, armazenamento isolado por usuário/organização,
controle de acesso real no backend, auditoria persistente, testes de carga, observabilidade,
integração com orquestrador por feature flags e testes ponta a ponta.

Estes componentes são fundações verificáveis, **não** oito agentes autônomos homologados.
