"""Governed proposals: never executes generated code or changes production."""
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import json
import re

@dataclass(frozen=True)
class Proposal:
    identifier: str
    target: str
    rationale: str
    patch: str
    author: str = "agent"
    status: str = "pending_review"

def propose(target: str, rationale: str, patch: str, author: str = "agent") -> Proposal:
    if not target or not rationale or not patch:
        raise ValueError("target, rationale and patch are required")
    if len(patch) > 100_000:
        raise ValueError("proposal too large")
    if Path(target).is_absolute() or ".." in Path(target).parts:
        raise ValueError("unsafe target")
    if not re.fullmatch(r"[a-zA-Z0-9_./-]+", target):
        raise ValueError("invalid target")
    digest = sha256((target + "\\0" + rationale + "\\0" + patch).encode()).hexdigest()[:16]
    return Proposal(digest, target, rationale, patch, author)

def export_review(proposal: Proposal, directory: str) -> Path:
    """Only stores a reviewable JSON proposal, never applies a patch."""
    dest = Path(directory)
    dest.mkdir(parents=True, exist_ok=True)
    output = dest / (proposal.identifier + ".json")
    if output.exists():
        raise FileExistsError("proposal already exists")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(asdict(proposal), stream, ensure_ascii=False, indent=2)
    return output
