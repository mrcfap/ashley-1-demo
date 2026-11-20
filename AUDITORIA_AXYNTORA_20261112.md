# Axyntora | Auditoria e autonomia operacional

Versão preparada em 12/11/2026 a partir do ZIP enviado por Marcelo.

## Autoconhecimento

O chat usa a identidade da persona selecionada e consulta o inventário de capacidades da API. Ao discutir a evolução da plataforma, recebe uma sugestão de verificação para a primeira lacuna entre conversa, memória longa, voz, visão, arquivos e vídeo. A prioridade segue essa ordem.

| Operação | Acesso | Resultado |
| --- | --- | --- |
| `GET /identidade?persona=Ashley` ou `?persona=Ashen` | Sessão autenticada conforme a política de acesso da API | Cinco perguntas, estado das capacidades e verificações sugeridas |
| `POST /identidade/reflexoes` | Administrador autenticado | Gera e registra uma proposta pendente com base no inventário do servidor. Retorna HTTP 409 quando a lista de lacunas está vazia. |

As duas rotas usam o cabeçalho `Authorization: Bearer <token>`. A reflexão fica em `data/identidade_evolutiva.sqlite3`. Para manter esses registros entre implantações, a pasta precisa estar em armazenamento persistente. A rotina de reflexão gera propostas sob demanda. A decisão e a aplicação de mudanças cabem ao responsável pelo projeto.

## Achados

- O prompt anterior sempre apresentava Ashley no bloco de identidade, inclusive nas sessões de Ashen. O nome agora acompanha a persona selecionada.
- O inventário procurava `/memoria/buscar`, enquanto a API registra `/memoria/buscar/{user_id}`. A rota e o estado de verificações sem sucesso foram corrigidos.
- O arquivo ativo de memória longa está sintaticamente válido e inclui retenção de 5.000 interações por usuário. O arquivo antigo com erro aparece como cópia legada em formato de texto.
- O ZIP de origem incluía configurações locais, um arquivo auxiliar de ambiente, bancos SQLite e capturas de câmera. Esses itens, os logs e as cópias administrativas ficaram fora da distribuição. O arquivo `.env.example` foi incluído para configuração. Para atualizar uma instalação existente, preserve o `.env` e os bancos do seu ambiente.
- O endpoint `/health` contém indicadores estáticos usados pela interface. Para consultar evidências registradas de funcionamento, use `/capacidades`. O histórico de evidências depende dos caminhos que registram resultados e pode exigir confirmação no ambiente atual.

## Validação

- A suíte automatizada passou com 270 testes e um aviso de depreciação de dependência.
- Os testes das novas rotas cobrem acesso sem sessão, identificação de Ashen, validação da persona, bloqueio de conta comum ao registrar uma reflexão e persistência de proposta pendente.
- A inicialização pelo ponto de entrada do Docker foi verificada localmente com configuração limpa. A memória SQLite foi verificada com dados sintéticos, incluindo retenção e separação entre usuários.
- Pendem testes no Windows e testes ao vivo de Ollama/Gemini, voz, câmera, serviços multimídia e Supabase. Esta entrega foi validada localmente e não foi publicada.
