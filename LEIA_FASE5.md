# Ashley 1.0 — Fase 5 (base supervisionada)

## Escopo efetivamente implementado
- `app/agents/autonomous/phase5.py`: planejamento validado e ponte para a Fase 4/V22. Reutiliza o fluxo existente de aprovação para geração de propostas; não promove alterações à produção nem executa testes de código gerado.
- `app/memory/semantic_memory_safe.py`: armazenamento e recuperação de embeddings fornecidos externamente, com validação de vetores, separação por usuário/modelo e conexões SQLite fechadas. **Não produz embeddings**, não oferece API e não autentica usuários.
- `tests/test_phase5.py`: testes locais de isolamento básico, vetores inválidos e plano sem alterações.

## Pendências deliberadas (não simular como prontas)
1. Integrar autenticação da Ashley e consentimento explícito antes de expor memória ou sensores por API.
2. Integrar serviço real de embeddings e migração/limpeza de dados, com política de retenção e exclusão.
3. Percepção multimodal real: adaptar o analisador já existente, com captura opt-in, limites de taxa e observações fundamentadas. O código enviado no chat retorna frases fixas e **não detecta riscos**.
4. Criar executor de testes em isolamento forte (container/sandbox com limites de CPU, rede, arquivos e tempo) antes de permitir testes automáticos de código gerado. `ast.parse` não é sandbox.
5. Registrar proveniência, confiança e validade temporal das memórias/observações; separar fato, inferência e hipótese. Integrar com V50.
6. Adicionar endpoints via APIRouter, jamais criar outro `FastAPI()` paralelo ou liberar endpoints sem controle de acesso.
7. Revisar a compatibilidade com V58/V59/V61 de acordo com interfaces reais; a presença de arquivos de motores não comprova sua integração funcional.

## Instalação
Faça backup. Extraia somente os arquivos novos do pacote sobre a raiz `Ashley Oficial final`. Nenhum arquivo existente foi substituído.

Execute na raiz do projeto:
```
python -m unittest discover -s tests -p "test_phase5.py" -v
```

Não há integração automática ao servidor principal nesta entrega. Não configure este protótipo como monitoramento de emergência.
