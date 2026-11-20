# Ashley V71 EMPATHY-ANAMNESIS + V72 RESONANCE-SILENCE

Entrega incremental: **nao substitui** o app.py. V71 armazena marcos fornecidos voluntariamente com consentimento e permite exclusao por titular. V72 oferece planejamento de tom e concisao mediante preferencia explicita. Nao faz inferencia de sentimentos, diagnostico ou simulacao de afeto.

## Instalacao
1. Faca backup da pasta Ashley Oficial final e pare o servidor.
2. Extraia este ZIP na raiz da pasta Ashley Oficial final, mantendo `app/`, `tests/` e `INSTALAR_V71_V72.py`.
3. `python -m unittest discover -s tests -p "test_v71_v72.py" -v`
4. `python INSTALAR_V71_V72.py`
5. `python -c "from app.API.app import app; print([p for p in app.openapi()['paths'] if '/v71/' in p or '/v72/' in p])"`
6. Execute a suite existente novamente.

## Limites e proximos passos
- API autenticada reutiliza `identity` da integracao V62-V65, incluindo a restricao atual a adultos.
- V71 nao envia lembretes, nao monitora aniversarios automaticamente e nao recupera historico sem consentimento.
- V72 devolve **instrucoes para o orquestrador**, nao altera o chat existente automaticamente.
- O sinal `urgent` e apenas um parametro do cliente: antes de uso no chat, integrar detector de riscos **no servidor**, independente desse sinal, e manter respostas essenciais em situacoes de seguranca.
- Necessario revisar LGPD, retencao, exportacao e revogacao de consentimento antes de producao.
- Nao instalar os esbocos originais como apps FastAPI independentes: seus IDs 69/70 conflitam com os motores ja nomeados e o codigo original produz falas ficticias.
