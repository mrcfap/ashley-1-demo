# Integração conservadora V77–V80 ao orquestrador

Este patch foi preparado para a versão Ashley Oficial final já atualizada com o pacote incremental V77–V80.

## Instalação
1. Pare o servidor (Ctrl+C) e faça backup da pasta Ashley Oficial final.
2. Extraia este ZIP sobre a raiz `Ashley Oficial final`, mantendo a estrutura de pastas. Substitua `app/core/orquestrador.py` quando solicitado.
3. Não copie `app_API_app.py.reference`: é somente uma referência da API analisada. Se o pacote incremental anterior não estiver instalado, instale-o primeiro.
4. Execute `python -m uvicorn app.API.app:app --host 127.0.0.1 --port 8000` na raiz.
5. Verifique `/docs` e a rota autenticada `/api/v1/engines/v77-v80/status`.

## Escopo real
- Orquestrador instancia FinaleBridge e devolve `finale_v77_v80` em `preparar_contexto`.
- Diagnóstico expõe `v77_v80` com capacidades e limitações.
- Nenhum consentimento é concedido automaticamente; nenhuma evidência é criada implicitamente; nenhuma missão externa é executada.
- V79 ainda não traduz, não reconhece idiomas e não sintetiza voz; exige provedores e testes específicos.
- V78 não faz isolamento completo entre organizações e revogação não interrompe tarefas externas.
- Não testado contra sua instalação Windows, credenciais ou serviços externos.
