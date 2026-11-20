# Axyntora — proteção de uploads (02/11/2026)

O sistema agora bloqueia preventivamente arquivos executáveis e scripts potencialmente ativos nas rotas `/arquivo/analisar` e `/documentos/gerar`. Não executa arquivos enviados. Gera SHA-256 e tenta acionar Microsoft Defender no Windows quando disponível. Em servidores Linux/Render, não há garantia de antivírus: use `ASHLEY_REQUIRE_AV=1` para bloquear uploads quando não houver verificação confiável (inclusive documentos). A ausência de detecção não garante ausência de malware.

## Testes
`python -m pytest tests/test_upload_security.py tests/test_arquivos_universais_extendido.py -q`

## Pendências para produção
- Integrar ClamAV/serviço antivírus isolado no Linux/Render.
- Implementar autenticação obrigatória em `/arquivo/analisar` (a rota original aceita `user_id` sem autenticação verificada).
- Limitar descompressão e razão de compressão de ZIP/EPUB e avaliar parser de documentos em sandbox.
- Realizar teste de ponta a ponta no Windows e Render.
- RAR/7Z não possuem parser habilitado neste pacote.

Não substitua seu projeto sem backup; teste em cópia primeiro.
