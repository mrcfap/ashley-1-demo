# Axyntora — Camada de confiança (implementação inicial)

Componentes: PROVENANCE (manifesto hash), COVENANT (contrato de autonomia), memória procedural versionada, ANIMA (ajuste opt-in), VINCULUM (acordos e promessas confirmadas).

## Execução
`python -m unittest discover -s tests -p test_trust_innovations.py -v`

## Limites explícitos
- Os módulos são bibliotecas locais; **não estão conectados** à API, AION SYMPHONY, banco de dados ou serviços externos.
- O manifesto PROVENANCE não é assinatura digital, prova de fonte verdadeira ou certificado jurídico.
- COVENANT aceita somente resultados marcados como verificados pelo chamador; precisa integrar verificação independente e ledger antes de uso real.
- A memória procedural usa armazenamento em RAM e aceita sinalizadores de testes fornecidos pelo chamador; precisa CI, persistência e segregação na camada de dados.
- ANIMA usa apenas estado declarado e consentimento explícito, sem análise emocional automática.
- VINCULUM não executa lembretes automaticamente; promessas são registros locais confirmados e podem ser apagados.
- A segregação por tenant neste protótipo não substitui autenticação, RLS, criptografia, auditoria e controles de acesso reais.
- Os arquivos `.env` e credenciais privadas foram excluídos do pacote distribuível; configure ambiente a partir de `.env.example`.
