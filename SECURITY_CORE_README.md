# Axyntora Security Core — primeira camada

Implementado: limitação local por IP e rota para autenticação/cadastro/recuperação de senha, cabeçalhos de segurança, testes unitários. Não há autoalteração de código nem monitoramento autônomo de incidentes nesta etapa.

## Limitações e implantação
- O limitador é **em memória por processo**: reinício limpa contadores; múltiplas instâncias não compartilham limites. Antes de produção, implementar Redis ou controle na borda (WAF/API gateway).
- Atrás de proxy, `request.client.host` pode ser o endereço do proxy; configure corretamente a cadeia de proxies confiáveis no servidor. Nunca confie indiscriminadamente em `X-Forwarded-For`.
- Ative `ASHLEY_FORCE_HTTPS=1` somente quando HTTPS estiver corretamente configurado em todos os subdomínios, pois ativa HSTS.
- Testar login, registro, recuperação de senha, CORS, câmera, microfone e frontend no ambiente real.
- Pendências: rate limit distribuído, revisão de permissões e isolamento de usuários, varredura de dependências, logs de incidentes sem dados pessoais, backup criptografado com restauração testada, proteção de agentes e pentest autorizado.
- ZIP gerado sem `.env`, SQLite, backups antigos, caches e arquivos temporários; preserve credenciais e dados locais separadamente.
