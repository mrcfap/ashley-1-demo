# Ashley 1.0 — Núcleo Cognitivo Experimental

Este pacote preserva o projeto recebido e adiciona `app/cognitive_growth/`.

## Capacidades
- Memória persistente SQLite de experiências e feedback.
- Estados afetivos **simulados**: curiosidade, satisfação, preocupação, frustração e empatia.
- Metacognição funcional: objetivos, atividade recente, decisão sugerida.
- Propostas de mudanças em código com registro de auditoria e revisão humana.

## Uso
```python
from app.cognitive_growth import CognitiveGrowthEngine
motor = CognitiveGrowthEngine()
motor.experience('A conversa foi útil', feedback=0.8)
motor.add_goal('Reduzir latência de resposta', priority=8)
print(motor.deliberate())
```

## Testes
`python -m pytest -q teste_nucleo_cognitivo.py`

## Limites e próximos passos
Este módulo não cria consciência, sentimentos subjetivos ou AGI. Não é conectado automaticamente ao endpoint `/chat`, nem modifica arquivos, executa comandos, treina modelos ou roda em background. Propostas aprovadas **ainda exigem** revisão, testes em ambiente isolado e aplicação manual. Para autonomia ativa: integrar explicitamente ao orquestrador existente, com consentimento, limites de recursos, observabilidade e desligamento. Nunca conceder acesso irrestrito a código, credenciais ou produção.

## Segurança
O ZIP original pode conter `.env`, bancos de dados e segredos. Revise antes de distribuir ou publicar.
