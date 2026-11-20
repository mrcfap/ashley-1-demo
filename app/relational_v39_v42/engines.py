"""Ashley V39–V42: cues are hypotheses, not emotion detection or sentience.
No autonomous external action; no raw conversations are stored here.
"""
from __future__ import annotations
import re
from typing import Any

class RelationalV39V42:
    VERSION = "39-42"
    def analisar(self, message: str, history: list | None = None, *, minor: bool = False) -> dict[str, Any]:
        text = (message or "")[:5000]
        lower = text.casefold()
        history = (history or [])[-8:]
        # Explicit self-reports only; no emotion or mental-health diagnosis.
        signals = {
            "frustracao": ("estou frustrado", "estou frustrada", "que raiva", "não aguento"),
            "tristeza_declarada": ("estou triste", "me sinto triste", "estou desanimado", "estou desanimada"),
            "alegria_declarada": ("estou feliz", "estou animado", "estou animada", "que alegria"),
            "urgencia": ("é urgente", "preciso agora", "urgente"),
        }
        evidencias = [k for k, patterns in signals.items() if any(p in lower for p in patterns)]
        pergunta = "?" in text
        planejamento = any(w in lower for w in ("planejar", "plano", "projeto", "estratégia", "estrategia"))
        preferencia = "objetiva" if any(w in lower for w in ("resuma", "seja breve", "direto ao ponto")) else "conversacional"
        if planejamento: preferencia = "analitica"
        if evidencias and preferencia == "conversacional": preferencia = "acolhedora_sem_inferencias"
        # A history is context only; avoid claims about past events absent clear evidence.
        temas = []
        for entry in history:
            if not isinstance(entry, dict): continue
            content = str(entry.get("content", ""))[:180]
            if entry.get("role") == "user" and content.strip(): temas.append(content)
        retomar = any(p in lower for p in ("voltando ao assunto", "como falamos", "lembra daquilo", "continuando"))
        pedido_proativo = any(p in lower for p in ("me lembre", "acompanhe", "pergunte depois", "retome depois"))
        return {
            "v39_sentir": {"sinais_declarados": evidencias, "modo_resposta": preferencia,
                "regra": "Sinais textuais não comprovam estado emocional; confirmar quando relevante."},
            "v40_presenca": {"expressao": "atenta", "ritmo": "calmo" if evidencias else "natural",
                "animacao": "sutil", "sincronizacao_fonetica": False},
            "v41_continuum": {"retomada_solicitada": retomar, "mensagens_usuario_recentes": len(temas),
                "regra": "Retomar somente informações presentes em histórico/memória autorizada."},
            "v42_horizonte": {"pedido_acompanhamento": pedido_proativo, "menor": minor,
                "pode_agir_sem_autorizacao": False,
                "regra": "Sem contato proativo, dependência afetiva, exclusividade ou ações externas sem consentimento."},
        }

    def instrucoes(self, result: dict[str, Any]) -> str:
        sentir=result["v39_sentir"]
        continuidade=result["v41_continuum"]
        return ("V39-V42 — ORIENTAÇÃO DE INTERAÇÃO (não são sentimentos reais nem ações realizadas):\n"
                f"V39: modo {sentir['modo_resposta']}; sinais textuais explícitos: {', '.join(sentir['sinais_declarados']) or 'nenhum'}. "
                "Acolha sem diagnosticar ou alegar ler emoções.\n"
                "V40: comunicação calorosa e natural; expressões do avatar são animações de interface, não emoções sentidas.\n"
                f"V41: retomada solicitada={continuidade['retomada_solicitada']}; use somente fatos presentes no contexto. "
                "Não invente lembranças nem prometa lembrar no futuro sem persistência confirmada.\n"
                "V42: iniciativa apenas com autorização; preserve autonomia, vínculos humanos, privacidade e limites. "
                "Nunca finja ser humano, consciente, apaixonado ou emocionalmente dependente. "
                "Não afirme ter executado ações externas sem confirmação de ferramenta.")
