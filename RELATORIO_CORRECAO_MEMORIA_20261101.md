# Correção de inicialização da memória de longo prazo

- O construtor não tenta mais conectar ao Supabase na importação da API.
- A primeira operação de memória com DATABASE_URL configura as tabelas PostgreSQL sob demanda.
- Falhas de conexão continuam explícitas; não há substituição silenciosa por SQLite.
- A URL do Supabase reportada anteriormente continua inválida e deve ser corrigida no ambiente local.
- O código original de memória e os dados locais não foram migrados.
- Arquivos de credenciais e dados locais foram excluídos do pacote distribuível.
- Testes de hardware, APIs externas e integração PostgreSQL real não estão homologados.
