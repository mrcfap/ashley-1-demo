"""Explicitly evaluated experience; no model-weight updates or autonomous execution."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Outcome:
    strategy: str
    passed: bool
    verified: bool

def consolidate(outcomes, minimum=3):
    scores = {}
    for event in outcomes:
        if event.verified:
            scores.setdefault(event.strategy, []).append(event.passed)
    return {key: {'samples':len(values), 'success_rate':sum(values)/len(values)}
            for key, values in scores.items() if len(values)>=minimum}

def analogies(source_edges, target_mapping):
    """Structural hypotheses only; caller must validate applicability."""
    return [{'source': (a, relation, b), 'hypothesis': (target_mapping[a], relation, target_mapping[b]), 'verified': False}
            for a, relation, b in source_edges if a in target_mapping and b in target_mapping]
