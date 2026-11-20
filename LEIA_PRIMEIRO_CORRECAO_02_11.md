# Correções de 02/11/2026 — Axyntora

- SQLite: fechamento explícito de conexões, inclusive quando há exceções; evita WinError 32 nos testes Windows.
- Upload: arquivos `.py` podem ser **lidos como dados**, nunca executados. O teste de política agora é independente do antivírus do computador.
- Falha ou detecção do antivírus continua bloqueando a análise; não foi desativada a proteção para passar testes.
- `pytest.ini`: define escopo do loop de fixtures assíncronas.

## Instalação
1. Faça backup da pasta atual. Extraia esta pasta em novo local.
2. Preserve seu `.env` fora do ZIP e copie-o manualmente.
3. Na raiz do projeto: `python -m pytest -q -ra`.
4. Valide o serviço e os recursos de câmera/voz no Windows antes de publicar.

**Limites:** testes no ambiente de empacotamento não substituem Defender real, serviços externos, nem homologação de produção.
