# Homologação e implantação
- Migração aditiva aplicada ao Supabase existente; não exclui dados.
- 8 testes específicos aprovados no pacote local.
- Suíte integral no ambiente de avaliação bloqueada pela dependência google-genai; usuário reportou 349 testes no Windows.
- Continuum experimental usa SQLite para métricas e exige adaptação PostgreSQL antes de produção.
- Persistência facial exige DATABASE_URL e ASHLEY_FACE_ENCRYPTION_KEY existentes e válidos no Render; não alterar chave sem migrar dados.
- Não publicar a branch experimental no serviço principal sem homologação.
