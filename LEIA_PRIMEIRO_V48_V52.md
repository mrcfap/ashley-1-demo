# Ashley consolidada — V44 a V52 (pré-integração)

Fonte: ZIP oficial com V44–V47 + pacote V52 Expandida. Arquivos originais de código preservados; V48–V51 adicionados como módulos isolados em `app/future_v48_v51/`.

**Atenção:** V48–V51 são implementações iniciais verificáveis, NÃO motores completos ou integrados à API/orquestrador. V52 foi incorporado como biblioteca, NÃO conectado automaticamente à aplicação. Não declarar produção pronta.

- V48: heurísticas por usuário com aprovação explícita; não há aprendizagem federada real.
- V49: cálculo de custo com preços fornecidos pelo chamador; não há telemetria automática.
- V50: sinalização de falta de evidências; não valida a veracidade das fontes nem detecta drift estatístico.
- V51: envelopes HMAC assinados; **não criptografa** e não sincroniza com a nuvem.
- V52: registro e auditoria de dependências e extensões de memória/pesquisa/políticas do pacote anterior.

O V44 chama-se SINAPSE, diferente do SYNAPSE V52. Ambos são preservados em namespaces separados.

Por segurança, este pacote **não inclui `.env`, bancos de dados, arquivos `.pyc`, nem pastas de trabalho temporárias**. Faça backup do original e preserve seu `.env` local. Nunca publique segredos.

## Testar

Na raiz: `python TESTE_V48_V52.py`.

## Próximas etapas

Integrar os serviços à autenticação existente, criar migrações, instrumentar custos reais, adicionar busca vetorial e provedor web, integrar com os fluxos da API, implementar sincronização criptografada e testar ponta a ponta antes de implantação.
