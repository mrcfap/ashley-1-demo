"""Inventário local não invasivo da arquitetura Axyntora.

Inspeciona arquivos Python sem importar/executar motores, abrir bancos ou consultar rede.
Não confunde presença com integração ou funcionamento.
"""
import ast
import re
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix='/arquitetura', tags=['Diagnóstico seguro'])
ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app'
SKIP_DIRS = {'__pycache__', '.git', '.venv', 'venv', 'tests', 'test', 'backups', 'backup', '.ashley_backups'}

# Referências de teste: caminhos reais do pacote, sem pressupor que o motor esteja ativo.
REFERENCIAS = {
    'agentes': {
        'Planejador': 'app/agents/planner.py',
        'Crítico': 'app/agents/critic.py',
        'Coordenação autônoma': 'app/agents/autonomous/coordinator.py',
        'Memória de prompts': 'app/agents/agent_prompt_memory_bridge.py',
        'Memória persistente (módulo)': 'app/services/memoria_compartilhada.py',
        'Visão computacional (módulo)': 'app/vision/motor_visao.py',
        'Evolução supervisionada (módulo)': 'app/axiom_v95_v100/supervised.py',
    },
    'motores': {
        'V23 Autoevolução (referência)': 'app/evolution/evolution_engine_v11.py',
        'V24 Psicologia (referência)': 'app/humanization/engines.py',
        'V25 Voz (referência)': 'app/services/texto_voz.py',
        'V26 Integração (referência)': 'app/integracao_v26/motores.py',
        'V27–V30 (referência)': 'app/future_engines/motores.py',
        'V58 LEGACY': 'app/legacy_v58/engine.py',
        'V59 NEUROPSYCHE': 'app/neuropsyche_v59/engine.py',
        'V61 PRAXIS': 'app/praxis_v61/engine.py',
        'V76 Humanity Core': 'app/humanity_v76/engine.py',
        'V77–V80': 'app/finale_v77_v80/bridge.py',
        'V85–V94': 'app/axiom_v85_v94/core.py',
        'V95–V100': 'app/axiom_v95_v100/core.py',
    },
}


def _inspect(path, label=None):
    rel = path.relative_to(ROOT).as_posix()
    result = {'nome': label or path.stem, 'arquivo': rel, 'carregado': 'não verificado',
              'integrado': 'não verificado', 'operacional': 'não verificado'}
    if not path.is_file():
        result['estado'] = 'não localizado'
        return result
    try:
        source = path.read_text(encoding='utf-8-sig')
        tree = ast.parse(source, filename=rel)
        symbols = [n.name for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
        result.update(estado='encontrado', sintaxe='válida', simbolos= symbols[:16])
    except (OSError, UnicodeError, SyntaxError) as exc:
        result.update(estado='falha estática', sintaxe='inválida ou ilegível', erro=type(exc).__name__)
    return result


def _versions_from_path(path):
    """Extrai apenas versões explicitamente nomeadas no caminho (não presume V1–V100)."""
    s = path.relative_to(ROOT).as_posix().lower()
    versions = set()
    for match in re.finditer(r'v(\d{1,3})(?:_v?(\d{1,3}))?', s):
        a, b = int(match.group(1)), match.group(2)
        if b is not None and int(b) >= a and int(b) - a <= 100:
            versions.update(range(a, int(b) + 1))
        else:
            versions.add(a)
    return sorted(v for v in versions if 1 <= v <= 100)


def diagnostico():
    files = sorted(p for p in APP.rglob('*.py') if not (set(p.relative_to(APP).parts) & SKIP_DIRS))
    items = [_inspect(p) for p in files]
    version_map = {v: [] for v in range(1, 101)}
    for p in files:
        for version in _versions_from_path(p):
            version_map[version].append(p.relative_to(ROOT).as_posix())
    versions = [
        {'versao': f'V{v}', 'estado': 'referência em arquivo' if paths else 'sem referência explícita no nome de arquivo',
         'arquivos': paths[:15], 'total_arquivos': len(paths), 'operacional': 'não verificado'}
        for v, paths in version_map.items()
    ]
    references = {group: [_inspect(ROOT / rel, name) for name, rel in mapping.items()]
                  for group, mapping in REFERENCIAS.items()}
    agents = [i for i in items if i['arquivo'].startswith('app/agents/')]
    motors = [i for i in items if any(k in i['arquivo'].lower() for k in ('motor', 'engine', 'orquestr', 'integration', 'integracao'))]
    return {
        'modo': 'somente leitura; sem importação de módulos ou chamadas externas',
        'escopo': 'arquivos Python do app, referências V1–V100 e agentes',
        'resumo': {'arquivos_python': len(items), 'sintaxe_valida': sum(i['estado'] == 'encontrado' for i in items),
                   'falhas_estaticas': sum(i['estado'] == 'falha estática' for i in items),
                   'agentes_arquivos': len(agents), 'motores_arquivos_candidatos': len(motors),
                   'versoes_com_referencia_no_caminho': sum(bool(v['total_arquivos']) for v in versions),
                   'operacionais_confirmados': 0},
        'referencias': references, 'versoes': versions,
        'agentes': agents, 'motores_candidatos': motors, 'componentes': items,
        'observacao': 'Inventário estático não confirma importação, inicialização, registro em runtime nem funcionamento. Ausência de versão no nome do arquivo não prova ausência de implementação.'
    }


@router.get('/diagnostico')
def consultar_diagnostico():
    return diagnostico()


@router.get('/resumo')
def consultar_resumo():
    d = diagnostico()
    return {'modo': d['modo'], **d['resumo'], 'observacao': d['observacao']}


def resposta_para_chat():
    d = diagnostico()
    r = d['resumo']
    lines = [
        'Inventário real da arquitetura Axyntora (somente leitura):',
        f"Arquivos Python analisados: {r['arquivos_python']}; sintaxe válida: {r['sintaxe_valida']}; falhas estáticas: {r['falhas_estaticas']}.",
        f"Arquivos em app/agents: {r['agentes_arquivos']}; candidatos a motores/integrações: {r['motores_arquivos_candidatos']}.",
        f"Versões V1–V100 com referência explícita no caminho: {r['versoes_com_referencia_no_caminho']} de 100.",
        'Referências solicitadas:',
    ]
    for group, items in d['referencias'].items():
        lines.append(group.capitalize() + ':')
        for item in items:
            lines.append(f"- {item['nome']}: {item['estado']} ({item['arquivo']}); operação não verificada")
    lines.append('Versões com arquivos nomeados: ' + ', '.join(v['versao'] for v in d['versoes'] if v['total_arquivos']))
    lines.append('Não executei motores nem serviços externos. Arquivo encontrado não significa carregado, integrado ou operacional. Consulte /arquitetura/diagnostico para a lista completa.')
    return '\n'.join(lines)


# Interface legada mantida para compatibilidade com os testes e consumidores anteriores.
# As referências são pistas de localização, nunca comprovação de operação.
COMPONENTES = {
    'agentes': {
        'Planejador': 'app/agents/planner.py',
        'Crítico': 'app/agents/critic.py',
        'Coordenação autônoma': 'app/agents/autonomous/coordinator.py',
        'Memória de prompts': 'app/agents/agent_prompt_memory_bridge.py',
    },
    'motores': {
        'V23 Autoevolução': 'app/evolution/evolution_engine_v11.py',
        'V24 Psicologia': 'app/humanization/engines.py',
        'V25 Voz': 'app/services/texto_voz.py',
        'V26 Integração': 'app/integracao_v26/motores.py',
        'V27 Música': 'app/future_engines/motores.py',
        'V28 Processamento musical': 'app/future_engines/motores.py',
        'V29 MACI': 'app/future_engines/motores.py',
        'V30 MECA': 'app/future_engines/motores.py',
        'V58 LEGACY': 'app/legacy_v58/engine.py',
        'V59 NEUROPSYCHE': 'app/neuropsyche_v59/engine.py',
        'V61 PRAXIS': 'app/praxis_v61/engine.py',
        'V76 Humanity Core': 'app/humanity_v76/engine.py',
        'V77 PILOT CORE': 'app/finale_v77_v80/bridge.py',
        'V78 Governança': 'app/finale_v77_v80/bridge.py',
        'V79 Linguagem Universal': 'app/finale_v77_v80/bridge.py',
        'V80 Missão Épica': 'app/finale_v77_v80/bridge.py',
        'V85 Aprendizado Contínuo': 'app/axiom_v85_v94/core.py',
        'V86 Evolução Adaptativa': 'app/axiom_v85_v94/core.py',
        'V90 Processamento Neuromórfico': 'app/axiom_v85_v94/core.py',
        'V94 IA Fisiológica': 'app/axiom_v85_v94/core.py',
    },
}

def inspecionar(nome, arquivo):
    """Compatibilidade: inspeciona caminho relativo sem executar código."""
    candidate = (ROOT / arquivo).resolve()
    if not candidate.is_relative_to(ROOT.resolve()):
        return {'nome': nome, 'arquivo': arquivo, 'estado': 'ausente', 'carregado': 'não verificado', 'operacional': 'não verificado'}
    result = _inspect(candidate, nome)
    if result['estado'] == 'não localizado':
        result['estado'] = 'ausente'
    return result

# Preserva o inventário ampliado e oferece a estrutura de consulta legada.
_diagnostico_ampliado = diagnostico
def diagnostico():
    report = _diagnostico_ampliado()
    report['modo'] = 'somente_leitura'
    report['grupos'] = {group: [inspecionar(name, path) for name, path in mapping.items()]
                        for group, mapping in COMPONENTES.items()}
    return report
