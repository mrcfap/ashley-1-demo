# Correção de voz e chat — Ashley 1.0

## Instalação
1. Pare o servidor (`Ctrl+C`). Preserve o backup existente.
2. Copie os três arquivos deste pacote para os caminhos correspondentes na **pasta ativa** da Ashley, substituindo os antigos:
   - `frontend/index.html`
   - `app/API/app.py`
   - `app/services/gemini_service.py`
3. **Não substitua** `.env`, `data/`, bancos de dados, orquestrador ou módulos de memória.
4. Reinicie: `py -m uvicorn app.API.app:app --reload --port 8000`.
5. Abra a página com Ctrl+F5 para limpar o cache.

## Comportamento
- A opção padrão de voz neural não recorre mais automaticamente à voz local. A opção **Local (sem cota)** continua disponível caso você a selecione manualmente.
- Em caso de falha neural, o texto permanece visível e aparece um aviso.
- O chat tenta cada modelo configurado uma vez, com limite de 25 segundos por modelo por padrão (`ASHLEY_MODEL_TIMEOUT_SECONDS`), e diferencia cota, timeout e indisponibilidade.
- O tempo total da rota `/chat` continua limitado por `ASHLEY_CHAT_TIMEOUT_SECONDS` (padrão 75 s).

## Limitações
- Esta correção não cria cota Gemini nem garante voz neural quando o serviço estiver indisponível.
- Chamadas bloqueantes da SDK executadas em threads podem continuar até concluir mesmo depois de um timeout do Python.
- Os testes locais não substituem testes reais no navegador e com Gemini.
- Se sua instalação servir outro `index.html`, confira o HTML servido pelo navegador antes de substituir qualquer outro arquivo.
