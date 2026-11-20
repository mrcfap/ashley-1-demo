import asyncio
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.tasks.motor_execucao_v22 import MotorExecucaoV22
from app.agents.autonomous.phase4 import CodingV22Bridge


class FakeCoder:
    def __init__(self):
        self.calls = 0

    async def propose_and_review(self, goal, files):
        self.calls += 1
        return {
            "id": "test",
            "workspace": "sandbox",
            "phase3_review": {"syntax_ok": True}
        }


def criar_motor(tmp):
    return MotorExecucaoV22(Path(tmp) / "v22.db")


def test_conclusao_nao_pode_substituir_cancelamento():
    with tempfile.TemporaryDirectory() as tmp:
        motor = criar_motor(tmp)
        tarefa = motor.criar(
            user_id=1, titulo="Teste",
            objetivo="Teste de cancelamento"
        )

        motor.proxima()
        motor.cancelar(tarefa["id"], 1)
        with pytest.raises(ValueError):
            motor.concluir(tarefa["id"], "Resultado")

        atual = motor.obter(tarefa["id"], 1)
        assert atual["status"] == "CANCELADA"


def test_recuperacao_de_tarefa_sem_tentativas_restantes():
    with tempfile.TemporaryDirectory() as tmp:
        motor = criar_motor(tmp)
        tarefa = motor.criar(
            user_id=1, titulo="Teste",
            objetivo="Recuperação",
            max_tentativas=1
        )

        with motor._conectar() as conn:
            conn.execute(
                "UPDATE tarefas_v22 SET status='EXECUTANDO', "
                "tentativas=1 WHERE id=?",
                (tarefa["id"],)
            )

        recuperado = MotorExecucaoV22(motor.db_path)
        recuperado.recuperar_interrompidas()
        atual = recuperado.obter(tarefa["id"], 1)

        assert atual["status"] == "FALHOU"


def test_reserva_concorrente_nao_duplica_tarefa():
    with tempfile.TemporaryDirectory() as tmp:
        motor = criar_motor(tmp)

        for i in range(2):
            motor.criar(
                user_id=1,
                titulo=f"Tarefa {i}",
                objetivo="Teste concorrente"
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(
                lambda _: motor.proxima(), range(2)
            ))

        ids = [r["id"] for r in resultados if r]

        assert len(ids) == 2
        assert len(set(ids)) == 2


def test_bridge_respeita_limite_de_tentativas():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "sample.py").write_text("x=1\n")

        coder = FakeCoder()
        bridge = CodingV22Bridge(root, coder=coder)

        tarefa = bridge.submit(
            1, "Teste de limite", ["sample.py"]
        )
        bridge.approve_generation(tarefa["id"], 1)

        with bridge.queue._conectar() as conn:
            conn.execute(
                "UPDATE tarefas_v22 SET tentativas=max_tentativas "
                "WHERE id=?",
                (tarefa["id"],)
            )

        with pytest.raises(ValueError):
            asyncio.run(
                bridge.run_approved(tarefa["id"], 1)
            )

        assert coder.calls == 0


def test_tarefa_cancelada_nao_pode_ser_reservada():
    with tempfile.TemporaryDirectory() as tmp:
        motor = criar_motor(tmp)
        tarefa = motor.criar(
            user_id=1, titulo="Teste",
            objetivo="Cancelamento"
        )

        motor.cancelar(tarefa["id"], 1)

        assert motor.proxima() is None
        assert motor.obter(tarefa["id"], 1)["status"] == "CANCELADA"


def test_falha_nao_reativa_tarefa_cancelada():
    with tempfile.TemporaryDirectory() as tmp:
        motor = criar_motor(tmp)
        tarefa = motor.criar(
            user_id=1, titulo="Teste",
            objetivo="Falha após cancelamento"
        )
        motor.proxima()
        motor.cancelar(tarefa["id"], 1)

        assert motor.falhar(tarefa["id"], "erro tardio") is False
        assert motor.obter(tarefa["id"], 1)["status"] == "CANCELADA"


def test_aprovacao_duplicada_e_rejeitada():
    with tempfile.TemporaryDirectory() as tmp:
        motor = criar_motor(tmp)
        tarefa = motor.criar(
            user_id=1, titulo="Teste",
            objetivo="Aprovação única",
            requer_aprovacao=True
        )
        motor.aprovar(tarefa["id"], 1)

        with pytest.raises(ValueError):
            motor.aprovar(tarefa["id"], 1)


def test_instanciar_motor_nao_recupera_tarefa_ativa_automaticamente():
    with tempfile.TemporaryDirectory() as tmp:
        motor = criar_motor(tmp)
        tarefa = motor.criar(
            user_id=1, titulo="Ativa",
            objetivo="Não reiniciar em cada instância"
        )
        motor.proxima()

        outra_instancia = MotorExecucaoV22(motor.db_path)

        assert outra_instancia.obter(tarefa["id"], 1)["status"] == "EXECUTANDO"


def test_bridge_preserva_cancelamento_durante_geracao():
    class CancelingCoder:
        def __init__(self):
            self.bridge = None
            self.task_id = None

        async def propose_and_review(self, goal, files):
            self.bridge.queue.cancelar(self.task_id, 1)
            return {
                "id": "cancelled-mission",
                "workspace": "isolated-test",
                "phase3_review": {"syntax_ok": True},
            }

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "sample.py").write_text("x=1\\n")
        coder = CancelingCoder()
        bridge = CodingV22Bridge(root, coder=coder)
        task = bridge.submit(1, "Teste cancelamento", ["sample.py"])
        coder.bridge = bridge
        coder.task_id = task["id"]
        bridge.approve_generation(task["id"], 1)

        with pytest.raises(ValueError):
            asyncio.run(bridge.run_approved(task["id"], 1))

        assert bridge.queue.obter(task["id"], 1)["status"] == "CANCELADA"
