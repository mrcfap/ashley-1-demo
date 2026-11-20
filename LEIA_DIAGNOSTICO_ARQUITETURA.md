# Diagnóstico seguro da arquitetura

Rotas autenticadas: GET /arquitetura/diagnostico e GET /arquitetura/resumo.

A interface de chat também responde a perguntas explícitas de inventário com dados locais, sem depender do Ollama.

O diagnóstico só verifica existência e sintaxe dos arquivos; **não comprova funcionamento, carregamento ou implementação integral**. Não importa módulos, não executa motores e não chama serviços externos.

Teste: `python -m pytest -q tests/test_architecture_diagnostics.py`

Para verificar o chat, faça login e pergunte: `Ashley, identifique seus motores e agentes e informe quais estão operacionais.`

Esta versão preserva o código de memória existente. Antes de substituir a pasta atual, mantenha cópia de segurança do banco de dados e do arquivo .env; nunca substitua os dados atuais por versões antigas do ZIP.
