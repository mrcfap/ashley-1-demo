# Auditoria Axyntora — 01/11/2026

## Alterações
- Módulo legado com sintaxe inválida movido para backup_legado como arquivo texto, sem perda de conteúdo.
- Novo executor PowerShell com parada obrigatória em caso de falha de dependências ou testes.
- Distribuição sanitizada, sem .env, bancos, dados biométricos, caches e arquivos locais.

## Resultado da suíte parcial

```text
........................................................................ [ 38%]
........................................................................ [ 76%]
............................................                             [100%]
188 passed in 1.23s

```

## Restrições de homologação
A suíte completa depende de bibliotecas não disponíveis neste ambiente (por exemplo google-genai). Não foi possível validar câmera e microfone físicos, voz TTS real, provedores de vídeo, música, serviços externos, nem persistência no Windows. Nenhum desses componentes é certificado como 100% homologado.

## Executar no Windows
Abra PowerShell na pasta e execute `./HOMOLOGACAO_WINDOWS.ps1`. Revise o log e valide manualmente hardware, credenciais, consentimento, persistência e integrações antes da liberação comercial.
