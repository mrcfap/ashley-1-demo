# Fundação humana: ELO + HORIZONTE VIVO + ESSENTIA

Implementação inicial isolada e determinística.

- ELO: preferência de interação escolhida explicitamente, mediante consentimento.
- HORIZONTE VIVO: comparação de cenários fornecidos pelo usuário e detecção de limites e dados ausentes.
- ESSENTIA: revisão de coerência com limites e valores declarados; sem inferir motivações.
- HumanFoundation: reúne as três avaliações, sempre sem autorizar execução.

Execução dos testes: `python -m unittest discover -s tests -p test_human_foundation.py -v`.

Não há conexão automática com API, banco, AION SYMPHONY, Decision Ledger ou Outcome Intelligence. Para produção: autenticação, isolamento multi-tenant, persistência versionada, consentimento revogável, proteção de dados e integração supervisionada.

O hash é um identificador de integridade, não assinatura digital.
