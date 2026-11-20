# Ashley 1.0 — Homologação offline, etapa 1

## Instalação
1. Faça backup da pasta Ashley Oficial final.
2. Extraia este pacote na raiz da pasta Ashley Oficial final.
3. No PowerShell, dentro da pasta, execute:
   `python ashley_offline_homologar.py`
4. Abra `relatorio_homologacao_offline.json`.

## O que faz
Verifica presença dos componentes principais, registros estáticos de rotas, simula contrato de chat (sem IA) e testa isolamento básico em banco SQLite **temporário**. Não altera app.py, os bancos reais, nem os 76 motores. Não acessa rede e não exige chave Gemini.

## Opcional: testes existentes
`python ashley_offline_homologar.py --com-testes`

**Atenção:** a opção de testes existentes carrega módulos do projeto e pode ler o `.env`. Por isso, esta opção NÃO garante ausência de chamadas externas, apesar de remover variáveis de chave herdadas do terminal. Use apenas em ambiente isolado de rede se for essencial garantir zero chamadas. A execução padrão não importa nenhum módulo da Ashley.

## Limites
- Simulação não equivale a conversa com IA real.
- Verificação estática não equivale a integração funcional.
- Não testa câmera, voz, imagem, vídeo, login HTTP, nem os 76 motores individualmente.
- Para homologação funcional sem Gemini, próximos passos: injeção de provedor de inferência, modelos locais, mocks por serviço, testes HTTP com TestClient e auditoria de chamadas externas.
