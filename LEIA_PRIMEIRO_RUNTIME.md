# Ashley Runtime + Mission Control — incremento seguro

Esta entrega é uma **base operacional local e somente leitura**, não um motor V77 e não uma implantação comercial.

## O que faz
- `runtime_report`: verifica a presença de componentes e bancos sem importar serviços, acessar rede, criar arquivos ou executar código.
- `mission_report`: lê a fila SQLite V22 filtrando pelo `user_id`, sem mostrar o objetivo da tarefa ou outros campos sensíveis.
- `ashley_mission_control.py`: painel textual local, sem endpoint público, sem alterar a aplicação principal.
- Testes de isolamento, não criação de dados e leitura segura.

## Instalação
1. Pare o servidor e faça backup da pasta.
2. Extraia este ZIP na raiz `Ashley Oficial final`, mantendo a estrutura.
3. Execute: `python -m unittest discover -s tests -p "test_ashley_runtime.py" -v`
4. Execute: `python -m unittest discover -s tests -p "test_*.py" -v`
5. Para diagnóstico local: `python ashley_mission_control.py`
6. Para consultar tarefas locais de um usuário autorizado: `python ashley_mission_control.py --user-id 1`

## Limites e segurança
- Não foi modificado `app/API/app.py`, `app/security/auth.py`, Gemini, V22, V76 ou bancos existentes.
- O painel CLI é **administrativo e local**. Não publique sua saída ou adicione uma rota HTTP sem autenticação/autorização robusta.
- `user_id` é argumento local, não autenticação. Em uma futura interface web, o identificador deverá vir do token autenticado.
- Verificação de presença não é health check de execução. Não faz recuperação automática, atualização ou rollback.
- Não copia `.env`, bancos, chaves ou dados de clientes.
- A integração com API, telemetria, recuperação supervisionada, limites de custo e atualização com rollback são **próximas etapas**, sujeitas a testes.
