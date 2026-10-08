# Ashley 1.0 — voz neural estável (Gemini + alternativa)

Este ZIP é uma cópia da pasta fornecida pelo usuário, com correções em `app/services/gemini_service.py`, `app/API/app.py` e `requirements.txt`.

## Instalação
1. Faça backup da pasta em uso e **não publique este ZIP**: ele pode conter `.env`, chaves e dados pessoais.
2. Pare o PowerShell com Ctrl+C.
3. Substitua a pasta ativa pelo conteúdo da pasta `Ashley oficial 1` deste ZIP (não crie uma pasta dentro de outra por engano).
4. Dentro da pasta que contém `requirements.txt`, execute `py -m pip install -r requirements.txt`. O `edge-tts` é novo e necessário.
5. Inicie `py -m uvicorn app.API.app:app --reload --port 8000`. Abra http://127.0.0.1:8000 e atualize com Ctrl+F5.

## Funcionamento
- Gemini TTS é tentado primeiro (tempo curto). Se falhar, tenta voz neural alternativa Edge TTS via internet.
- A voz alternativa não usa a cota Gemini, mas depende de um serviço externo e da rede; não há garantia de disponibilidade.
- Se ambos falharem, a resposta fica por escrito; a voz robótica **não** é ativada automaticamente.
- O erro de conversa `/chat` é separado do TTS. Cota esgotada pode continuar impedindo respostas novas.
- O ZIP conserva os arquivos do usuário, inclusive `.env` e bancos de dados, exatamente como fornecidos. Não compartilhar nem publicar em Git.
