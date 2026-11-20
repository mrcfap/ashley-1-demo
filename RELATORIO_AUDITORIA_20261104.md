# Auditoria técnica — Ashley 1.0

## Escopo
Arquivo recebido: Ashley Oficial final.zip. Auditoria estática de Python e execução da suíte pytest no ambiente de análise.

## Resultados
- ZIP de entrada: 799 entradas, teste de integridade sem erro.
- Falha inicial: ImportError na coleta de tests/test_cognitive_growth.py: classes CognitiveGrowth e EmotionalState não exportadas pelo pacote.
- Correção: exportação explícita de CognitiveGrowthEngine, CognitiveGrowth e EmotionalState em app/cognitive_growth/__init__.py.
- Suíte completa após correção: **255 passed em 5,20 segundos** (avisos suprimidos no comando de teste).
- AST: 265 arquivos Python examinados, zero erros de sintaxe (ignorando backups).

## Limites e pendências
- Testes unitários não equivalem à homologação ponta a ponta dos motores V1–V100, câmera, voz, vídeo, geração de mídia, endpoints autenticados e provedores externos.
- O núcleo cognitivo implementa estados afetivos **simulados**, registro de eventos, objetivos e propostas de mudança. Não há evidência de sentimentos subjetivos ou AGI.
- O motor de evolução não aplica código automaticamente: a revisão registra aprovação para teste manual, sem deploy.
- Não foi validado serviço persistente de reflexão agendada, nem integração do núcleo com a rota principal de chat.
- A pasta original contém arquivos .env e backups potencialmente sensíveis. Evitar distribuir o ZIP publicamente e revisar/rotacionar credenciais antes de publicação.

## Comandos reproduzíveis
```bash
python -m pytest -q --disable-warnings --maxfail=10
```
