"""Ciclo de avaliação offline e supervisionado. Não aplica código nem executa testes arbitrários."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from app.evolution.continuous_agent_architecture import ContinuousEvolution

ALLOWED_METRICS = {
    'vision_latency_ms': (1200, 'vision', 'Reduzir a latência da visão', 'Medir latência p50/p95 com imagens de teste'),
    'language_mismatch_rate': (0.01, 'language', 'Manter resposta e voz no idioma escolhido', 'Testar sessões em português, mandarim e árabe'),
    'memory_recall_rate': (0.95, 'memory_recall', 'Melhorar recuperação da memória com consentimento', 'Testar recuperação após reinício e isolamento de usuários'),
    'response_latency_ms': (3000, 'chat_latency', 'Reduzir tempo de resposta', 'Medir p50/p95 sem perda de qualidade'),
}

def run_cycle(root: str | Path, metrics_path: str | Path) -> dict:
    """Lê métricas numéricas locais de um JSON e propõe melhorias, sem autoaplicar."""
    root = Path(root).resolve()
    source = Path(metrics_path).resolve()
    if not source.is_file() or source.stat().st_size > 100_000:
        raise ValueError('Arquivo de métricas inexistente ou grande demais')
    metrics = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(metrics, dict):
        raise ValueError('Métricas devem ser objeto JSON')
    engine = ContinuousEvolution(root)
    generated = []
    for key, (threshold, component, benefit, test) in ALLOWED_METRICS.items():
        if key not in metrics:
            continue
        value = metrics[key]
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not (0 <= value < 1e9):
            raise ValueError('Métrica inválida: ' + key)
        triggered = value < threshold if key == 'memory_recall_rate' else value > threshold
        if triggered:
            candidate = engine.observe(component, f'{key}={value}; referência={threshold}',
                'Investigar gargalo e propor melhoria com dados de teste', benefit, test, 'medium')
            generated.append(candidate['identifier'])
    summary = {'timestamp': datetime.now(timezone.utc).isoformat(), 'evaluated': sorted(k for k in metrics if k in ALLOWED_METRICS), 'proposals': generated, 'applied_changes': 0}
    audit = root / '.ashley_evolution_reviews' / 'cycle_audit.jsonl'
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(summary, ensure_ascii=False) + '\n')
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--metrics', required=True)
    args = parser.parse_args()
    print(json.dumps(run_cycle(args.root, args.metrics), ensure_ascii=False, indent=2))
