"""Fase 4: ponte opt-in com V22. Não altera arquivos de produção."""
from __future__ import annotations
import json
from pathlib import Path
from app.tasks.motor_execucao_v22 import MotorExecucaoV22

KIND = 'ashley_coding_phase4'

class CodingV22Bridge:
    def __init__(self, project_root, db_path=None, coder=None):
        self.root = Path(project_root).resolve()
        self.queue = MotorExecucaoV22(db_path or self.root / 'ashley_coding_v22.db')
        self.coder = coder  # lazy: não instancia Gemini ao apenas enfileirar

    def recover_after_restart(self) -> int:
        """Chamado uma única vez no bootstrap do worker que possui esta fila."""
        return self.queue.recuperar_interrompidas()

    def submit(self, user_id: int, goal: str, files: list[str]):
        if not isinstance(user_id, int) or user_id < 1 or not goal.strip():
            raise ValueError('Usuário e objetivo obrigatórios')
        if not isinstance(files, list) or not 1 <= len(files) <= 4 or len(set(files)) != len(files):
            raise ValueError('Informe de 1 a 4 arquivos distintos')
        clean = []
        for file in files:
            if not isinstance(file, str): raise ValueError('Caminho inválido')
            p = (self.root / file).resolve()
            if not p.is_relative_to(self.root) or p.is_symlink() or not p.is_file() or p.suffix != '.py' or p.stat().st_size > 18000:
                raise ValueError('Arquivo fora do escopo, inexistente ou grande demais')
            clean.append(p.relative_to(self.root).as_posix())
        return self.queue.criar(user_id=user_id, titulo='Proposta de código Ashley', objetivo=goal,
            requer_aprovacao=True, max_tentativas=1,
            metadados={'kind': KIND, 'files': clean, 'approval_scope': 'gerar_proposta_apenas'})

    def approve_generation(self, task_id: str, user_id: int):
        task = self.queue.obter(task_id, user_id)
        if not task or task['metadados'].get('kind') != KIND:
            raise ValueError('Tarefa não encontrada')
        if task['status'] != 'AGUARDANDO_APROVACAO':
            raise ValueError('Tarefa não está aguardando aprovação')
        return self.queue.aprovar(task_id, user_id)

    async def run_approved(self, task_id: str, user_id: int):
        from app.tasks.motor_execucao_v22 import _agora

        task = self.queue.obter(task_id, user_id)
        if (
            not task
            or task['metadados'].get('kind') != KIND
            or not task['aprovado']
            or task['status'] != 'PENDENTE'
        ):
            raise ValueError('Tarefa inexistente ou não aprovada')

        # Reserva atômica por ID; a condição no SQL é a autoridade final.
        with self.queue._conectar() as conn:
            cur = conn.execute("""
                UPDATE tarefas_v22
                   SET status='EXECUTANDO',
                       tentativas=tentativas+1,
                       iniciado_em=COALESCE(iniciado_em, ?),
                       atualizado_em=?,
                       progresso=5,
                       etapa_atual='Entregue ao executor'
                 WHERE id=?
                   AND user_id=?
                   AND status='PENDENTE'
                   AND aprovado=1
                   AND tentativas < max_tentativas
            """, (_agora(), _agora(), task_id, user_id))
            if cur.rowcount != 1:
                raise ValueError(
                    'Tarefa já reservada, cancelada ou sem tentativas disponíveis'
                )

        try:
            # Importação tardia mantém a fila utilizável sem inicializar Gemini.
            if self.coder is None:
                from app.agents.autonomous.phase3 import AutonomousCodingPhase3
                coder = AutonomousCodingPhase3(self.root)
            else:
                coder = self.coder

            result = await coder.propose_and_review(
                task['objetivo'], task['metadados']['files']
            )

            report = {
                'mission_id': result['id'],
                'review': result['phase3_review'],
                'workspace': result['workspace'],
                'production_modified': False,
                'requires_human_review': True,
                'sandbox_tests_executed': False
            }

            # Uma tarefa cancelada durante a chamada externa não pode ser
            # reportada como concluída. concluir() também aplica CAS no SQL.
            atual = self.queue.obter(task_id, user_id)
            if not atual or atual['status'] != 'EXECUTANDO':
                raise ValueError('Execução cancelada ou alterada antes da conclusão')

            self.queue.concluir(task_id, report)
            return report
        except Exception as exc:
            self.queue.falhar(
                task_id, f'{type(exc).__name__}: {exc}'
            )
            raise
