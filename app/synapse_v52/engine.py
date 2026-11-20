"""V52 SYNAPSE: verificação de integração sem executar código arbitrário.
Sem alterações no sistema, deploy ou acesso a segredos.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Mapping
import json

@dataclass(frozen=True)
class MotorSpec:
    name: str
    version: str
    dependencies: tuple[str, ...] = ()
    probe: Callable[[], bool] | None = field(default=None, compare=False, repr=False)

class SynapseV52:
    def __init__(self):
        self._motors: dict[str, MotorSpec] = {}

    def register(self, motor: MotorSpec) -> None:
        if not motor.name or not motor.version:
            raise ValueError('Nome e versão obrigatórios')
        if motor.name in self._motors:
            raise ValueError(f'Motor duplicado: {motor.name}')
        self._motors[motor.name] = motor

    def audit(self) -> dict:
        statuses = {}
        for name, motor in sorted(self._motors.items()):
            missing = sorted(set(motor.dependencies) - self._motors.keys())
            statuses[name] = {'version': motor.version, 'missing_dependencies': missing,
                              'probe': 'not_configured', 'status': 'blocked' if missing else 'registered'}
        visiting, visited, cycles = set(), set(), set()
        def visit(name, path):
            if name in visiting:
                cycles.add(' -> '.join(path[path.index(name):] + [name])); return
            if name in visited: return
            visiting.add(name)
            for dep in self._motors[name].dependencies:
                if dep in self._motors: visit(dep, path + [dep])
            visiting.remove(name); visited.add(name)
        for name in self._motors: visit(name, [name])
        for name, motor in self._motors.items():
            if motor.probe is not None:
                try:
                    ok = motor.probe()
                    statuses[name]['probe'] = 'passed' if ok is True else 'failed'
                    if ok is not True: statuses[name]['status'] = 'blocked'
                except Exception as exc:
                    statuses[name]['probe'] = 'error'
                    statuses[name]['status'] = 'blocked'
                    statuses[name]['error_type'] = type(exc).__name__
        return {'engine': 'V52 SYNAPSE', 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                'motors': statuses, 'dependency_cycles': sorted(cycles),
                'certified': bool(statuses) and not cycles and all(v['status'] != 'blocked' and v['probe'] == 'passed' for v in statuses.values())}

    def report_json(self) -> str:
        return json.dumps(self.audit(), ensure_ascii=False, indent=2)
