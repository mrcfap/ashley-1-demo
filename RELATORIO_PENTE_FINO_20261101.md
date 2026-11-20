# Auditoria técnica Axyntora — 01/11/2026

## Escopo e evidência
Fonte: ZIP recebido em 01/11/2026 às 14:05 (nome do arquivo 140521).
Arquivos Python verificados: 248; erros de sintaxe: 0.
Testes selecionados: ..................................................                       [100%]
50 passed in 0.31s

## Correções
- Arquivo legado truncado preservado em backup_legado como texto, retirado da execução Python.
- Requisições JSON inválidas passam a receber HTTP 400 no middleware de autenticação, em vez de erro interno não tratado.
- Arquivos sensíveis locais (.env, bancos de dados, perfis faciais e uploads) excluídos do pacote para distribuição segura.
- Script AUDITORIA_EXECUTAR.ps1 criado para execução da suíte completa no Windows.

## Pendências de homologação
- Suíte completa não foi coletada neste ambiente por falta de google-genai (6 erros de importação).
- Câmera, microfone, TTS, modelos externos, música, vídeo, geração de arquivos e persistência de memória precisam de ensaios ponta a ponta no Windows com credenciais e hardware.
- Aprovação de testes unitários não demonstra que cada motor V1–V100 esteja ativo e operacional.
- Revisão de segurança, permissões por usuário, biometria e consentimento ainda necessária antes de produção pública.

## Limite da certificação
**Não homologado integralmente.** O pacote é uma versão corrigida com verificações reproduzíveis, não um certificado de 100% de funcionamento.
