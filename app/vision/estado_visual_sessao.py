from datetime import datetime, timedelta
from threading import RLock
from typing import Any, Dict, Optional


class EstadoVisualSessao:
    """
    Mantém temporariamente o último contexto visual validado de cada usuário.

    Não é memória permanente.
    O estado expira automaticamente após um período configurável.
    """

    def __init__(self, validade_minutos: int = 5):
        self.validade = timedelta(minutes=validade_minutos)
        self._estados: Dict[int, Dict[str, Any]] = {}
        self._lock = RLock()

    def registrar(
        self,
        user_id: int,
        reconhecimento: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra o resultado mais recente do reconhecimento visual.
        """

        agora = datetime.now()

        classificacao = reconhecimento.get("classificacao")
        identidade = (
            reconhecimento.get("identidade")
            if classificacao == "conhecido"
            else None
        )

        estado = {
            "user_id": user_id,
            "origem": "visao_local",
            "classificacao": classificacao,
            "identidade": identidade,
            "melhor_candidato": reconhecimento.get("melhor_candidato"),
            "similaridade": reconhecimento.get("similaridade"),
            "confianca_deteccao": reconhecimento.get("confianca_deteccao"),
            "registrado_em": agora.isoformat(),
            "expira_em": (agora + self.validade).isoformat(),
        }

        with self._lock:
            self._estados[user_id] = estado

        return dict(estado)

    def obter(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retorna o estado visual somente enquanto ele estiver válido.
        """

        with self._lock:
            estado = self._estados.get(user_id)

            if not estado:
                return None

            expira_em = datetime.fromisoformat(estado["expira_em"])

            if datetime.now() >= expira_em:
                self._estados.pop(user_id, None)
                return None

            return dict(estado)

    def limpar(self, user_id: int) -> bool:
        """
        Remove manualmente o contexto visual de um usuário.
        """

        with self._lock:
            return self._estados.pop(user_id, None) is not None

    def limpar_todos(self) -> None:
        """
        Remove todos os estados visuais temporários.
        """

        with self._lock:
            self._estados.clear()

    def estado(self, user_id: int) -> Dict[str, Any]:
        """
        Retorna informações operacionais sobre a sessão visual.
        """

        atual = self.obter(user_id)

        return {
            "ativo": atual is not None,
            "user_id": user_id,
            "validade_segundos": int(self.validade.total_seconds()),
            "contexto": atual,
        }