# Axyntora | Atualização de vídeo

A geração de vídeo usa `gemini-omni-1.2-flash` pela Interactions API do Google. A integração pede um clipe de oito segundos, respeita a proporção e a resolução escolhidas e salva o MP4 para download autenticado. O botão e os pedidos do chat continuam usando o acompanhamento por tarefa. O comando já usado no PowerShell continua aceito em `POST /video/gerar`.

A configuração aceita o modelo novo explicitamente. Se a instalação tiver um dos três IDs Veo 3.1 Preview desativados em `GEMINI_VIDEO_MODELS`, a aplicação usa o Omni automaticamente. A chave do Google e os bancos locais ficam na instalação existente.

## Aplicar no Windows

1. Pare o servidor com Ctrl+C. Extraia a pasta nova e preserve o `.env` e os dados da instalação anterior.
2. Na pasta do projeto, execute `python -m pip install -r requirements.txt` e reinicie com `python -m uvicorn app.API.app:app --reload`.
3. No segundo PowerShell, confira o modelo ativo:

   ```powershell
   (Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health').models.video
   ```

   Para a configuração padrão, o resultado esperado é `gemini-omni-1.2-flash`.

4. Repita o teste de geração e abra o MP4 baixado. O acesso e a cota do Omni dependem do projeto Google da sua chave.

## Verificação desta entrega

A suíte passou com 276 testes e um aviso de depreciação de dependência. A integração local usou o SDK real do Google com transporte simulado. Foram verificados o corpo do pedido ao Omni, as duas rotas de vídeo, o download do MP4 e a separação entre contas. O teste ao vivo com a conta Google da instalação permanece pendente.

- [Guia de geração de vídeo](https://ai.google.dev/gemini-api/docs/video)
- [Documentação do Gemini Omni Flash](https://aistudio.google.com/docs/omni)
