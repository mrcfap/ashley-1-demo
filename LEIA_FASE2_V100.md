# Axyntora V100 — Fase 2: deliberação supervisionada

## Instalação
Faça backup da pasta Ashley Oficial final. Pare o Uvicorn. Extraia o ZIP **dentro da pasta raiz do projeto**, substituindo `app/axiom_v95_v100/api.py` e adicionando `app/axiom_v95_v100/supervised.py` e `tests/test_v100_supervised.py`. Nenhum outro arquivo é alterado.

Execute `python -m pytest tests/test_v100_supervised.py tests/test_v95_v100.py -q` e inicie `python -m uvicorn app.API.app:app --reload`.

## O que faz
`POST /api/v1/engines/v100/mission/{id}/deliberate` com corpo `{"data":{"consent":true,"use_local_model":true,"sources":[]}}`. O campo `use_local_model` é opcional e falso por padrão. Quando verdadeiro, solicita **três análises independentes** ao Ollama local `qwen3:1.7b`: Ashley (proposta), Ashen (crítica), Auditor (checagem). Requer Ollama funcionando em `127.0.0.1:11434`. Caso falhe, retorna plano baseado em regras e `offline_rules_fallback`. O processamento ocorre sob demanda, não em segundo plano.

`GET /api/v1/engines/v100/mission/{id}/report` recupera missão e última deliberação. Ambos os endpoints exigem autenticação, usam ID do usuário da sessão e armazenam resultados no SQLite já existente V95–V100.

## Limites de segurança e escopo
Não acessa a internet, não executa código arbitrário, não modifica arquivos nem realiza implantação. V98/V99 são **selecionados para planejamento**, não executados. As fontes são fornecidas pelo usuário e não verificadas externamente. As respostas de Ashley/Ashen são chamadas independentes ao modelo local; não são agentes com ferramentas ou autoengenharia. A etapa de execução supervisionada com sandbox e ferramentas exige implementação e validação posteriores. O V100 ainda não está ligado automaticamente ao `/chat`.

## Exemplo no Console do Chrome (sessão autenticada)
```javascript
fetch('/api/v1/engines/v100/mission/6a95eb28-df4e-4527-9407-a9c3d08158cf/deliberate', {
  method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'},
  body:JSON.stringify({data:{consent:true,use_local_model:true,sources:[]}})
}).then(async r=>{console.log('HTTP',r.status);console.log(await r.json())}).catch(console.error)
```

**Observação:** se a requisição demorar ou cair em fallback, execute novamente com `use_local_model:false` para verificar o fluxo de regras. Cada uma das três chamadas locais possui timeout de 12 segundos.
