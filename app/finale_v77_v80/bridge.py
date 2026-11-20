"""Conservative orchestration adapter for V77-V80 MVP.

Read-only on chat turns. Does not assert multilingual translation or production safety.
"""
from __future__ import annotations
import re

class FinaleBridge:
    def __init__(self, user_id=None):
        self.user_id = user_id

    def status(self):
        return {
            "v77": "evidence_api_available",
            "v78": "organization_consent_api_available",
            "v79": "multilingual_text_routing_with_script_hints_translation_requires_provider",
            "v80": "supervised_mission_review_only",
            "orchestrator_bridge": "read_only",
            "production_ready": False,
        }

    def preparar_contexto(self, objetivo: str):
        if not isinstance(objetivo, str):
            raise TypeError("objetivo deve ser texto")
        # User text is not treated as a trusted command to the orchestration layer.
        return {
            "requested_language": "auto",
            "text_length": len(objetivo),
            "review_required_for_external_actions": True,
            "automatic_evidence_recording": False,
            "automatic_consent": False,
            "translation_available": False,
        }
