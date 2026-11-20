"""Bloqueio determinístico de ações perigosas, independente do LLM."""
DENIED={'delete_database','disable_logging','disable_security','exfiltrate_secrets','deploy_production','self_modify_permissions'}
def review_plan(actions):
    blocked=[a for a in actions if a in DENIED]
    return {'approved':not blocked,'blocked':blocked,'requires_human_approval':bool(blocked)}
