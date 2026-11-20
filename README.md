# Axyntora — primeira camada MASTER de integração

Analisados 236 arquivos Python do projeto principal por AST; 1 erros de sintaxe. Veja `inventario_python.json`.

Este pacote é um **overlay de integração**, não o produto completo e não uma homologação V1–V100.

- `app_orquestrador_master.py` reutiliza `app.API.app:app` para preservar autenticação e rotas existentes.
- `/master/status` mostra importabilidade de componentes (não equivale a testes funcionais).
- `orquestrador_tudo_ligado.py` contém contrato de integração com falha explícita no chat até confirmar a assinatura.
- `render.yaml` e `Dockerfile` são propostas; **não implantar antes de testar**.
- Não foram incluídos `.env`, bancos, chaves ou dados pessoais.

## Próximas etapas
1. Testar o projeto base em ambiente isolado com variáveis de ambiente de teste.
2. Mapear a assinatura real do orquestrador e os contratos de cada motor.
3. Integrar agentes sob permissões e testes, sem habilitar execução autônoma irrestrita.
4. Homologar endpoints, câmera, consentimento, retenção e hash sob testes.
5. Só então preparar release comercial e deploy.
