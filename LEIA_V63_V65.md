# Ashley — V63, V64 e V65 (base incremental)

Este pacote é uma **primeira implementação isolada**, sem mudanças nos arquivos existentes, sem novas rotas públicas e sem execução automática. Extraia os arquivos na raiz `Ashley Oficial final`.

## Motores
- **V63 PSYCHE-SYNAPSE**: apoio à organização com base apenas na carga **autodeclarada**, mediante consentimento. Não diagnostica burnout, não monitora empregados, não infere emoções por áudio ou vídeo.
- **V64 REALITY BRIDGE**: ciclo `PLANEJADO -> AGUARDANDO_VERIFICACAO -> CONFIRMADO_POR_PESSOA`; exige evidência e confirmação humana. Nesta versão usa memória RAM, não SQLite/V22.
- **V65 EPISTEMIC CORE**: classifica a origem de alegações e exige evidência para uma marcação declarada de verificação. Não executa verificação externa sozinho.

## Testar no PowerShell
`python -m unittest discover -s tests -p "test_v63_v65.py" -v`

## Integrações seguintes
1. Adaptar para `APIRouter` da aplicação principal, usando autenticação e autorização do usuário real.
2. Persistir registros com fechamento correto de conexões, políticas de retenção e exclusão.
3. Conectar V64 à fila V22 e ao mecanismo de aprovação autenticada, com trilha de auditoria.
4. Conectar V65 a fontes de evidência reais e ao V50/V60; não tratar afirmações do agente como evidência.
5. Vincular V63 a ações opt-in, sem diagnóstico ou vigilância.
6. Executar testes E2E da aplicação real e validação da visão, sem respostas simuladas.

**Não declarar os motores integrados ao servidor, nem homologados em produção, somente porque os testes unitários passaram.**
