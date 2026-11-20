"""V43/V45/V49: roteamento de texto híbrido, opcional e sem ações externas.
Não altera o ECOS existente. Privacidade local é uma política explícita.
"""
from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Callable, Awaitable

log = logging.getLogger("axyntora.ecos_router")

@dataclass
class RouterResult:
    text: str
    model: str
    provider: str
    elapsed_seconds: float

class EcosV43Router:
    def __init__(self, cloud: Callable[..., Awaitable[tuple[str,str]]],
                 local: Callable[..., Awaitable[tuple[str,str]]],
                 *, cloud_timeout=30., local_timeout=90., cooldown=60.,
                 max_failures=2, local_first=False):
        self.cloud, self.local = cloud, local
        self.cloud_timeout = float(cloud_timeout)
        self.local_timeout = float(local_timeout)
        self.cooldown = float(cooldown)
        self.max_failures = max(1, int(max_failures))
        self.local_first = bool(local_first)
        self._failures = 0
        self._retry_after = 0.
        self.metrics = {"cloud_success": 0, "cloud_failure": 0, "local_success": 0, "local_failure": 0}

    async def arbitrar_e_executar(self, *, system: str, message: str, history=None,
                                  private=False, allow_cloud=True, prefer_local=None) -> RouterResult:
        # Dados privados nunca seguem para a nuvem, nem em fallback.
        local_only = private or not allow_cloud
        first_local = local_only or (self.local_first if prefer_local is None else bool(prefer_local))
        now = time.monotonic()
        if now < self._retry_after and not local_only:
            first_local = True
        order = ["local"] if local_only else (["local", "cloud"] if first_local else ["cloud", "local"])
        last_error = None
        for provider in order:
            if provider == "cloud" and time.monotonic() < self._retry_after:
                continue
            started = time.monotonic()
            try:
                fn = self.local if provider == "local" else self.cloud
                timeout = self.local_timeout if provider == "local" else self.cloud_timeout
                answer, model = await asyncio.wait_for(
                    fn(system=system, message=message, history=history or []), timeout=timeout)
                if not isinstance(answer, str) or not answer.strip():
                    raise ValueError("Resposta vazia do provedor")
                self.metrics[provider + "_success"] += 1
                if provider == "cloud":
                    self._failures = 0
                    self._retry_after = 0.
                return RouterResult(answer, str(model), provider, time.monotonic()-started)
            except Exception as exc:
                last_error = exc
                self.metrics[provider + "_failure"] += 1
                if provider == "cloud":
                    self._failures += 1
                    if self._failures >= self.max_failures:
                        self._retry_after = time.monotonic() + self.cooldown
                log.warning("Falha no provedor %s: %s", provider, type(exc).__name__)
        raise RuntimeError("Nenhum provedor de IA disponível") from last_error
