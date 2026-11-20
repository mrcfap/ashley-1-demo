# Axyntora | Auditoria multimodal de 12/11/2026

A atualização parte de Ashley Oficial final(20261112-125427).zip.

| Fluxo | Problema encontrado | Correção |
| --- | --- | --- |
| Chat | Pedidos diretos de criação seguiam para o modelo conversacional | A interface encaminha pedidos explícitos de imagem, vídeo, música e documento às rotas de geração. Os botões continuam disponíveis. |
| Imagem | A prévia pedia o arquivo protegido sem o token. A integração também interrompia a tentativa após erro de modelo | A prévia usa download autenticado. O serviço extrai os bytes do retorno do SDK, preserva o formato PNG, JPG ou WebP e tenta o próximo modelo quando aplicável. |
| Vídeo | A interface aguardava toda a operação em uma única requisição. O retorno do download do SDK era descartado | A interface acompanha o trabalho em requisições curtas e baixa o MP4 autenticado. A rota síncrona anterior permanece disponível para outros clientes. |
| Música | A interface principal não acionava um gerador de música | O botão e o chat acionam o Lyria 3.5. A interface reproduz o MP3 e oferece o download. |
| Documentos | A geração e a análise dependiam do Gemini mesmo com Ollama configurado. O campo de análise era ignorado pela interface | Os fluxos seguem o provedor de texto configurado. A interface exibe a análise e oferece downloads autenticados em PDF, Word, PowerPoint, Excel, TXT, Markdown e CSV. |

A API mantém arquivos e tarefas separados por conta. Mensagens de erro de geração descrevem situações como chave ausente, limite de cota, tempo excedido e resposta inválida. O acompanhamento de vídeo e música usa a memória do processo e expira após uma hora da conclusão. Reiniciar o servidor encerra o acompanhamento de tarefas pendentes.

## Como aplicar no Windows

1. Extraia o ZIP e use a pasta `Ashley Oficial final`. Preserve o `.env` e os bancos da sua instalação. O ZIP de entrega exclui configurações locais, dados de conta, logs, capturas e perfis faciais.
2. Atualize as dependências com `py -m pip install -r requirements.txt`.
3. Para usar texto e documentos localmente, mantenha o Ollama aberto com o modelo configurado. `ASHLEY_CHAT_PROVIDER=ollama` usa o Ollama. `ASHLEY_CHAT_PROVIDER=gemini` usa o Google e respeita a configuração de fallback para Ollama.
4. Para imagem, vídeo e música, configure `GEMINI_API_KEY` com uma chave de projeto que tenha acesso aos modelos e cota. Os modelos padrão são Gemini 3.1 Flash Image, Gemini Omni 1.2 Flash e Lyria 3.5. Consulte `.env.example` para os parâmetros.
5. Inicie com `py -m uvicorn app_orquestrador_master:app --host 127.0.0.1 --port 8000` e abra `http://127.0.0.1:8000`.

## Verificação

A suíte do projeto passou com 273 testes e um aviso de depreciação. Os testes de integração HTTP passaram pelo servidor real e usaram respostas simuladas do Gemini, Veo, Lyria e Ollama. Verificaram JPG, MP4, MP3, os sete formatos de documentos, análise de anexo, mensagem de cota e isolamento entre contas. Os scripts das três cópias da interface foram executados com DOM simulado contra a API local. A reprodução no navegador e a geração ao vivo no Google ou no Ollama instalado do usuário ainda precisam de validação. O ZIP recebido não forneceu uma chave Google utilizável para testes ao vivo.

- [Geração de imagens pelo Gemini](https://ai.google.dev/gemini-api/docs/generate-content/image-generation)
- [Geração de vídeo pelo Google](https://ai.google.dev/gemini-api/docs/video)
- [Geração musical pelo Lyria](https://ai.google.dev/gemini-api/docs/music-generation)
