# Auditoria e correções — 30/10/2026

- Removidos `app/memory/memoria_longa_com_erro.py` e `.py.disabled`, ambos incompletos.
- Mantido intacto `app/memory/memoria_longa.py`.
- Adicionado `app/governance/decision_ledger.py`: componente **experimental e opt-in** para trilha de decisões com hash encadeado, evidências por referência e aprovação explícita.
- Adicionado teste unitário isolado. O módulo não foi conectado à API nem aos motores, evitando alterar o funcionamento existente.
- **Limites:** hash encadeado detecta alterações acidentais, mas não impede reescrita por administrador; escrita simultânea requer lock/transação; não armazenar segredos; não é sistema de conformidade certificado.
- É necessário testar o servidor, APIs externas, autenticação, memória e mídia no ambiente real antes de uso em produção.
- Os motores V77–V100 do catálogo fornecido não têm especificação individual confirmada no PDF; não foram tratados como homologados.
