from app.nextgen.engines import SymphonyV84
from app.nextgen.nextgen_planning import select_nextgen


class SymphonyOrchestratorBridge:
    """
    Integração inicial V84 -> OrquestradorAshley.

    Modo somente planejamento:
    - Não executa ferramentas.
    - Não altera arquivos.
    - Não concede autorizações.
    - Não interpreta flags do cliente como aprovação confiável.
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.symphony = SymphonyV84()

    @staticmethod
    def _nextgen_catalog():
        from app.axiom_v85_v94.core import catalog
        from app.axiom_v95_v100.core import catalog as catalog_v100
        return catalog() + catalog_v100()

    def prepare(self, objective, complexity="baixa"):
        if not isinstance(objective, str) or not objective.strip():
            raise ValueError("Objetivo deve ser texto não vazio")

        if complexity not in ("baixa", "media", "alta"):
            raise ValueError("Complexidade inválida")

        selection = self.orchestrator.selecionar_motores_cognitivos(
            objective,
            complexidade=complexity
        )

        return {
            "motor": "V84 SYMPHONY",
            "mode": "planning_only",
            "objective": objective,
            "selected_engines": selection,
            "execution_authorized": False,
            "external_actions_enabled": False,
            "nextgen_capability_catalog": self._nextgen_catalog(),
            "nextgen_selected_engines": select_nextgen(objective),
            "nextgen_selection_method": "transparent_keyword_heuristic_no_execution",
            "nextgen_execution": "disabled_planning_only",
            "requires_trusted_policy_check": True,
            "requires_human_approval_for_sensitive_actions": True,
        }
