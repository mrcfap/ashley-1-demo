# V79 Multilíngue — entrega incremental

Base: ZIP Ashley Oficial final(20261030-211316).zip, preservado integralmente, com alterações localizadas.

Implementado: normalização de 11 idiomas, preferência explícita, fallback, pistas de escrita não latina, adaptadores injetáveis de detecção/tradução, instrução de resposta para LLM, rotas autenticadas `/api/v1/engines/v79/languages`, `/v79/language/prepare`, `/v79/language/translate`, testes unitários.

**Limitações reais:** o V79 não possui detecção confiável de idiomas com alfabeto latino sem provedor externo; não faz tradução real sem configurar um provedor; não implementa reconhecimento de fala ou síntese de voz; a instrução multilíngue ainda precisa ser ligada ao pipeline de chat do aplicativo e homologada ponta a ponta. A rota de tradução devolve 503 quando o provedor não está configurado (não inventa tradução). Sem promessas de suporte universal.

Próxima etapa: integrar LLM/STT/TTS reais com preferências persistidas por usuário e testes de áudio/texto.
