# Axyntora — atualização e homologação local (14/11/2026)

## Implementação
- Motor de pragmática humana expandido: pistas de humor, metáfora, ironia, reparo de entendimento, escuta sem conselho, objetividade, pedido de análise e confirmação antes de agir.
- Integração já existente com `/chat` para Ashley e Ashen preservada.
- Pistas efêmeras, sem gravação adicional nem alegação de sentimentos subjetivos.
- Diferencial de produto **proposto**: contrato de conversa contextual, com respeito ao modo de interação pedido pelo usuário e reparo sem defensividade. Não há prova de exclusividade mundial.

## Verificações executadas
- `python -m pytest tests/test_pragmatica_humana.py tests/test_pragmatica_contextual.py -q`: **8 aprovados**.
- Suíte geral: **não homologada**. A coleta de testes falhou por ausência da dependência `google.genai` no ambiente de testes (6 erros na coleta em `tests/`; também ocorre em `test_video_offline.py`).
- Não foram executados testes reais com câmera, TTS, Gemini, Ollama, banco Supabase ou Render. Não houve deploy.

## Segurança do pacote
- Excluídos arquivos `.env` com credenciais, bancos locais, backups de usuários, caches e arquivos de log do ZIP de entrega.
- Configurar credenciais por variáveis de ambiente, usando `.env.example` como modelo, sem colocar chaves no Git.
- Como o ZIP original continha credenciais, recomenda-se **revogar/rotacionar as chaves expostas** antes de qualquer publicação.

## Próximos passos de homologação
1. Criar ambiente virtual e instalar dependências de `requirements.txt` e, quando aplicável, `requirements_multimodal.txt`.
2. Executar `python -m pytest -q` e corrigir todas as falhas.
3. Testar `/health`, autenticação, `/chat` nas duas personas, persistência, voz, visão e fluxos de consentimento em ambiente de homologação.
4. Revisar alterações e implantar apenas após aprovação manual.
