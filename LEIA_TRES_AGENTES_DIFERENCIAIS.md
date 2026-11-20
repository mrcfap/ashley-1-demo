# Axyntora — Três agentes diferenciais (FRONTIER_10–12)

Este pacote preserva os oito agentes de aprimoramento existentes e adiciona três agentes experimentais:

- **PARALLAX**: análise estruturada por cinco perspectivas; lacunas e riscos exigem revisão humana. Não executa decisões.
- **SEEDBANK**: cápsulas de conhecimento isoladas por tenant, concessão explícita e revogação em memória. Para produção, requer banco persistente, criptografia, autenticação real e auditoria imutável.
- **SYMBIOSIS**: compara medições antes/depois de tarefas realizadas independentemente pelo usuário, sem inferir causalidade.

Executar testes: `python -m unittest discover -s tests -p test_frontier_differentials.py -v`

**Limites:** testes unitários não equivalem a homologação de integração. Nenhum dos três está ligado ao AION SYMPHONY, APIs, bancos ou provedores externos. Os nove agentes de fronteira discutidos anteriormente permanecem especificações e não foram implementados por este pacote. O ZIP enviado mais recentemente pelo usuário estava vazio; foi utilizado o último pacote íntegro de oito agentes.
