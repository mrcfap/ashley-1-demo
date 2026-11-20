# Correção do erro google.genai.Client

A inicialização da visão agora falha de forma controlada se o SDK Gemini estiver incompatível. Isso evita que o import da API interrompa toda a suíte. A visão Gemini ficará indisponível até o SDK ser corrigido.

No PowerShell, dentro da pasta, com o ambiente virtual ativado se houver:

```powershell
python -m pip uninstall -y google-genai
python -m pip install --upgrade --force-reinstall google-genai pytest-asyncio
python -c "from google import genai; print(genai.__file__); print(hasattr(genai, 'Client'))"
python -m pytest -q
```

A verificação do Client deve mostrar True. Se aparecer False, confira conflitos de pacotes e interpretadores. O teste de regressão `tests/test_visao_inicializacao_segura.py` passou neste ambiente. A suíte completa e o acesso real ao Gemini não foram homologados aqui.

**Segurança:** este ZIP não inclui o `.env` nem credenciais. Copie o `.env` da sua instalação anterior para a nova pasta, sem compartilhá-lo. Faça backup antes de substituir.
