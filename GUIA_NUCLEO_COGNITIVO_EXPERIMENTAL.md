# Núcleo cognitivo experimental Ashley

Adicionado em `app/cognitive_growth/` sem modificar as rotas ou motores existentes.

**O que faz:** registra eventos locais, atualiza variáveis emocionais simuladas, calcula reflexão simples a partir de feedback e registra propostas de melhoria pendentes de revisão humana.

**O que NÃO faz:** sentir emoções reais, provar consciência, aprender pesos do modelo, alterar código, executar comandos, publicar mudanças ou garantir AGI.

**Uso:**
```python
from app.cognitive_growth import CognitiveGrowth, EmotionalState
state = EmotionalState()
print(state.update(success=True, novelty=.9, risk=.1))
core = CognitiveGrowth('ashley_growth.sqlite3')
core.record('feedback', {'success': True})
print(core.reflect())
print(core.propose('Melhorar testes', 'Criar mais casos de regressão antes da integração'))
```

**Integração futura:** conectar somente a eventos autorizados do orquestrador, filtrar dados pessoais, aplicar retenção/consentimento, adicionar avaliador com métricas e sandbox para testes de código. Aprovação humana obrigatória antes de implantar alterações.

**Testes:** `python -m pytest tests/test_cognitive_growth.py -q`
