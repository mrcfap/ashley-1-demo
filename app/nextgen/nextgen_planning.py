"""Ponte de catálogo e seleção V85–V94 para o V84; sem execução de motores."""
from __future__ import annotations
import re
from app.axiom_v85_v94.core import catalog
from app.axiom_v95_v100.core import catalog as catalog_v100, select as select_v100

KEYWORDS = {
 85: ('memória','memoria','aprender','consolidar','conhecimento','lembrar'),
 86: ('cenário','cenario','simular','contrafactual','causal','probabilidade'),
 87: ('código','codigo','programar','refatorar','bug','corrigir','software'),
 88: ('previsão','previsao','acompanhar','desvio','meta','resultado'),
 89: ('pesquisar','investigar','hipótese','hipotese','evidência','evidencia'),
 90: ('latência','latencia','desempenho','custo','orçamento','orcamento','recurso'),
 91: ('privacidade','dados pessoais','sigilo','consentimento','segurança','seguranca'),
 92: ('tom','linguagem','acolhedor','empatia','comunicação','comunicacao'),
 93: ('agentes','delegar','dividir tarefas','equipe','paralelo'),
 94: ('integrar','integração','integracao','orquestrar','capacidades','compor'),
}

def extended_inventory(legacy: dict) -> dict:
    """Mantém evidências históricas e anexa catálogo funcional limitado, sem fingir homologação."""
    result = dict(legacy)
    newer = catalog() + catalog_v100()
    old = list(legacy.get('engines', []))
    result['range'] = 'V1-V100'
    result['legacy_range'] = legacy.get('range', 'V1-V84')
    result['engines'] = old + [
        {'motor': e['id'], 'name': e['name'], 'symbol_references': ['app/axiom_v85_v94/core.py' if int(e['id'][1:]) <= 94 else 'app/axiom_v95_v100/core.py'],
         'status': e['status'], 'capabilities': e['capabilities'],
         'execution_verified': False, 'requires_authentication': e['requires_authentication']}
        for e in newer
    ]
    result['nextgen'] = newer
    result['files_parsed_attempted'] = legacy.get('files_parsed_attempted', 0)
    result['method'] = 'legacy_static_ast_plus_explicit_nextgen_registry'
    result['all_engines_operational'] = False
    return result

def select_nextgen(objective: str, *, limit: int = 5) -> list[dict]:
    """Seleção heurística transparente; não invoca nem executa motores."""
    if not isinstance(objective, str) or not objective.strip():
        raise ValueError('Objetivo obrigatório')
    text = objective.casefold()
    found = []
    available = {e['id']:e for e in catalog()}
    for number, words in KEYWORDS.items():
        matches = [word for word in words if re.search(r'(?<!\w)' + re.escape(word) + r'(?!\w)', text)]
        if matches:
            engine = available[f'V{number}']
            found.append({'id': engine['id'], 'name': engine['name'], 'matched_terms': matches,
                          'selection_method':'keyword_heuristic', 'planned_only': True,
                          'executed': False, 'requires_review': True})
    found.sort(key=lambda x:(-len(x['matched_terms']),int(x['id'][1:])))
    # New engines are selected independently; old behavior remains unchanged.
    remaining = max(0,limit-len(found))
    return (found[:limit] + [{**e,'planned_only':True,'requires_review':True} for e in select_v100(objective,limit=remaining)])[:limit]
