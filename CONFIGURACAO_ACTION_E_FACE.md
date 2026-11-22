# Axyntora Action + persistência facial

## Cadastro facial
No Windows, o cadastro facial legado em .npz continua disponível. No Render, configurar DATABASE_URL (PostgreSQL) e ASHLEY_FACE_ENCRYPTION_KEY (Fernet) para gravar vetores biométricos cifrados. Sem esses segredos, o cadastro retorna persistencia_facial_nao_configurada em vez de prometer persistência. Gere a chave com:

python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Não publique a chave no GitHub. Preserve a chave ao longo dos deploys, pois perdê-la torna os dados ilegíveis. Perfis de implantações anteriores que já foram perdidos não podem ser recuperados.

## Navegação (primeira etapa)
Endpoint autenticado POST /action/web/inspect com JSON {"url":"https://example.com"}.
Por padrão, nenhum domínio é autorizado. Configure ASHLEY_BROWSER_ALLOWED_DOMAINS=example.com,outro.com.
Somente leitura HTTPS pública; não envia formulários, não mantém cookies e bloqueia rede interna.
No Windows: python -m playwright install chromium
No Render: configurar navegador remoto com ASHLEY_BROWSER_CDP_URL ou imagem/container com Chromium instalado.
Este módulo é a base de um agente de sites, não automação completa de login e envio.

## Próximos passos
OAuth de Gmail/Outlook, WhatsApp Business API oficial, sessões isoladas por usuário, ações supervisionadas e testes de ponta a ponta.
