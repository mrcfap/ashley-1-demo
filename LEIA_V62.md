# Ashley V62 — PRAXIS-NEXUS (base incremental)

Este pacote complementa V63–V65. Copie `app/engines_v62/` e `tests/test_v62_nexus.py` para a raiz do projeto. Não sobrescreve arquivos existentes.

Execute na raiz: `python -m unittest discover -s tests -p "test_v62_nexus.py" -v`.

Implementado: cadastro de projetos, etapas, isolamento por proprietário, relato de evidências e confirmação explícita do proprietário. Banco SQLite com transações e fechamento garantido, sem dependências extras.

**Ainda não integrado:** rotas FastAPI, autenticação real, V22, auditoria central, interface, agentes e notificações. A aplicação deve derivar `owner_id`/`approver_id` da sessão autenticada, jamais confiar em IDs enviados pelo cliente. Evidências são descrições fornecidas por pessoas e não verificação automática de fatos. Nenhuma tarefa externa é executada por este módulo.
