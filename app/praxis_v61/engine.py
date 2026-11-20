"""V61: apoio à autonomia humana, consentimento e transferência de competências."""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class AgencyPlan:
    objective: str
    next_step: str
    user_choice: str
    assistant_role: str
    requires_confirmation: bool
    outcome_metric: str

class PraxisV61:
    def plan(self, *, objective: str, options: list[str], user_choice: str | None = None,
             sensitive_action: bool = False, outcome_metric: str = 'Usuário confirma resultado') -> dict:
        if not isinstance(objective,str) or not objective.strip(): raise ValueError('objetivo obrigatório')
        if not isinstance(options,list) or not options or not all(isinstance(x,str) and x.strip() for x in options):
            raise ValueError('opções concretas obrigatórias')
        if user_choice is not None and user_choice not in options: raise ValueError('escolha fora das opções')
        choice=user_choice or 'Aguardando decisão do usuário'
        step=(f'Executar somente após confirmação: {user_choice}' if sensitive_action and user_choice
              else (f'Preparar passo reversível: {user_choice}' if user_choice else 'Apresentar alternativas e consequências'))
        return asdict(AgencyPlan(objective,step,choice,'Facilitar, explicar e apoiar; não decidir pelo usuário',
                                 bool(sensitive_action or user_choice is None),outcome_metric))
