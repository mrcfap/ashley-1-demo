# Evolução pragmática da Axyntora — 14/11/2026

Implementado `app/pragmatics/engine.py`, integrado ao prompt do endpoint `/chat` em `app/API/app.py` para Ashley e Ashen. Pistas leves de humor, metáfora, ironia explícita, comentário casual, correção de entendimento e incerteza. Sem guardar mensagens, sem diagnóstico emocional e sem ações externas. O modelo continua responsável por interpretar contexto; heurísticas podem falhar.

**Teste:** `python -m pytest tests/test_pragmatica_humana.py -q`.

**Implantação:** pacote local para revisão; não enviado ao GitHub, Render ou Supabase. Testar regressão completa e conversas reais em ambiente de homologação antes de produção.

**Limites:** não produz sentimentos subjetivos nem comprova singularidade mundial. Diferencial proposto: coerência pragmática, respeito à intenção e reparo de entendimento, com medição futura por avaliações humanas e testes adversariais.
