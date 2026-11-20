# Ashley 1.0 V76 — Adequação comercial preliminar (14/10/2026)

## O que foi efetivamente alterado

- `app/API/app.py`: em `ASHLEY_COMMERCIAL_MODE=1`, desativa a criação administrativa inicial pela internet, impede login e chamadas autenticadas de menores e confere IDs de usuário em caminhos conhecidos, parâmetros de consulta e uploads multipart.
- `app/security/auth.py`: em modo comercial, impede novos cadastros de menores e alterações de perfil que resultem em conta de menor.
- `app/security/commercial_guard.py`: verificações de escopo de identidade.
- `tests/test_commercial_guard.py`: seis testes unitários novos.

**Não foram alterados** o modelo de IA, bancos de dados, credenciais, dados de usuários, frontend ou motores V1–V76. O modo comercial é DESATIVADO por padrão para evitar mudanças inesperadas no desenvolvimento. Não habilite um serviço público apenas com este patch.

## Instalação (PowerShell)

1. Pare o servidor Uvicorn e faça cópia da pasta original (incluindo bancos e `.env`) em LOCAL SEGURO, fora de repositórios e compartilhamentos.
2. Extraia este ZIP na raiz `Ashley Oficial final`, mantendo as subpastas. A substituição abrange `app/API/app.py` e `app/security/auth.py`; compare diferenças antes de instalar se editou os arquivos depois do ZIP de 14/10/2026 às 16:02.
3. Execute `python -m unittest discover -s tests -p "test_commercial_guard.py" -v`.
4. Execute `python -m unittest discover -s tests -p "test_*.py" -v`.
5. Teste cadastro, login, chat, upload, câmera, memória, agentes e API com usuários de teste separados.
6. Para validar o modo comercial LOCALMENTE, em PowerShell: `$env:ASHLEY_COMMERCIAL_MODE="1"` e reinicie o Uvicorn. Não exponha o serviço à internet ainda.
7. Para retornar ao modo de desenvolvimento: `Remove-Item Env:ASHLEY_COMMERCIAL_MODE -ErrorAction SilentlyContinue` e reinicie o processo.

**Aviso:** com modo comercial ativado, `/auth/register-first` fica desativado. Crie e teste uma conta administrativa adulta no ambiente LOCAL de desenvolvimento antes de habilitar esse modo. Usuários menores preexistentes não são excluídos; ficam bloqueados no login e nas chamadas protegidas. Não remova dados sem definir política de retenção e comunicação.

## Evidências e limitações

- Seis testes novos executados neste ambiente: aprovados. Análise sintática dos arquivos Python alterados: aprovada.
- A suíte completa anterior do usuário tinha 44 testes aprovados. A execução completa neste ambiente NÃO pôde ser concluída, pois não há `google-genai` instalado aqui. **Não afirmar que 50/50 passou no Windows até executar lá.**
- O middleware original tem ampla superfície de rotas; os caminhos enumerados cobrem alguns casos conhecidos, não todas as rotas e plugins. A auditoria de autorização precisa continuar.
- A verificação etária atual depende da data de nascimento declarada; NÃO constitui verificação robusta de idade. Não resolve sozinha o risco de acesso por menores.
- O projeto precisa de revisão de fluxos reais, ameaças, controles de acesso por objeto, rate limiting, monitoramento, gestão de segredos, dependências, licenças, LGPD, contratos e testes externos.
- O ZIP de origem contém `.env` e arquivos `.db`/`.sqlite3`. Não compartilhe esse ZIP com terceiros; se chaves reais foram expostas, considere revogação e rotação.

## Pendências para comercialização

1. **Jurídico:** confirmar termos do provedor efetivamente contratado, abrangência territorial, dados enviados, modalidade de pagamento, público-alvo e restrições de idade. A API Gemini tem restrição expressa a clientes direcionados ou provavelmente acessados por menores (termos de 23/03/2026).
2. **LGPD:** definir controlador/operador, finalidade/base legal por categoria, minimização, retenção, exclusão, direitos dos titulares, resposta a incidentes, transferência internacional, contato de privacidade e contratos de tratamento.
3. **Segurança:** auditar todas as rotas por IDOR/BOLA, autenticação, CSRF quando pertinente, limitação de tentativas, upload, exposição de documentos e controle de ações dos agentes.
4. **Dependências:** gerar SBOM com versões instaladas, licenças e avisos de vulnerabilidades. `requirements.txt` tem versões abertas e não comprova a licença de cada dependência transitiva.
5. **Operação:** separar ambientes, backups criptografados, restauração testada, métricas de custos, logs sem dados pessoais, observabilidade, suporte, política de incidentes e piloto controlado.
6. **Produto:** integração real dos motores e agentes, testes de carga, fluxos ponta a ponta, revisão de comunicação comercial e documentação do cliente.

## Fontes oficiais para revisão jurídica

- https://openai.com/policies/terms-of-use/
- https://ai.google.dev/gemini-api/terms
- https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados

Esta entrega é um reforço técnico preliminar, não homologação para produção nem parecer jurídico.
