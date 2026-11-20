# Ashley 1.0 — V76 Humanity Core (módulo independente)

## Escopo implementado
- Consentimento explícito por usuário; revogação e exclusão de dados V76.
- Objetivos individuais e registros de progresso em SQLite, com isolamento por usuário.
- Separação entre registros confirmados com evidência declarada e notas sem evidência.
- Propostas determinísticas e explicáveis sem executar ações externas.
- API FastAPI opcional com autenticação obrigatória delegada ao sistema existente.
- Não chama Gemini nem OpenAI; o provedor Gemini existente permanece intacto.

## Limites honestos
- NÃO implementa interpretação psicológica, empatia inferida, automação real, coordenação dos 75 motores ou UI.
- `verified_outcomes` conta registros confirmados com campo evidência; não significa verificação independente.
- O router NÃO é registrado automaticamente, pois depende de integrar o autenticador real da Ashley.
- Não usar diretamente em produção sem autenticação, política para menores, testes de integração, revisão de privacidade e segurança.

## Instalação segura
1. Pare o Uvicorn e faça backup do projeto.
2. Extraia o ZIP na raiz `Ashley Oficial final` (contém `app/humanity_v76/` e `tests/test_v76_humanity.py`). Não substitui arquivos existentes.
3. Na raiz do projeto execute:
   `python -m unittest discover -s tests -p "test_v76_humanity.py" -v`
4. Execute a bateria completa:
   `python -m unittest discover -s tests -p "test_*.py" -v`

## Integração futura, após inspecionar o app.py e autenticação reais
```python
from app.humanity_v76 import HumanityCoreV76
from app.humanity_v76.api import make_router

# Definir `get_authenticated_user_id` usando a autenticação EXISTENTE.
# A função DEVE validar a sessão/token e devolver o ID do usuário autenticado.
engine = HumanityCoreV76('data/v76_humanity.db')
app.include_router(make_router(engine, get_authenticated_user_id))
```
Nunca implementar `get_authenticated_user_id` lendo um `user_id` enviado pelo cliente.

## Próxima etapa
Fornecer `app/API/app.py` e o módulo de autenticação atual (sem senhas, tokens ou chaves), para conectar V76 ao backend e orquestrador sem quebrar a aplicação.
