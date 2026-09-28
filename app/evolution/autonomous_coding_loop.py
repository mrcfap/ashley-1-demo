from __future__ import annotations
import json
import re
from pathlib import Path

class AutonomousCodingLoop:
    """
    V10 — conecta propostas de evolução ao SelfCodingEngine.

    O modelo escolhe um alvo e produz código candidato. Este módulo:
    - monta contexto limitado do próprio projeto;
    - valida a resposta estruturada;
    - impede caminhos fora do projeto/áreas protegidas;
    - cria workspace;
    - aplica candidato somente no sandbox;
    - executa validação/testes;
    - devolve diff e decisão técnica.
    """

    def __init__(self, self_coder):
        self.self_coder = self_coder

    def _selecionar_arquivos(self, proposta, limite=8):
        inventario = self.self_coder.inventario(limite=500)
        componente = str(proposta.get("componente") or "").lower()
        problema = str(proposta.get("problema") or "").lower()
        tokens = set(re.findall(r"[a-zA-Z_]{4,}", componente + " " + problema))

        pontuados = []
        for item in inventario:
            arq = item["arquivo"]
            low = arq.lower()
            score = sum(1 for t in tokens if t in low)
            if componente and componente in low:
                score += 5
            if low.endswith(".py"):
                score += 1
            pontuados.append((score, arq))
        pontuados.sort(key=lambda x: (-x[0], x[1]))
        return [a for _, a in pontuados[:limite]]

    def contexto_para_modelo(self, proposta):
        arquivos = self._selecionar_arquivos(proposta)
        fontes = []
        for arq in arquivos:
            try:
                conteudo = self.self_coder.ler_arquivo(arq, max_chars=14000)
                fontes.append({"arquivo": arq, "conteudo": conteudo})
            except Exception:
                pass

        return {
            "proposta": proposta,
            "arquivos_relevantes": fontes,
            "regras": [
                "Produza exatamente uma alteração pequena e reversível.",
                "Não altere .env, credenciais, autenticação, permissões, bancos ou governança.",
                "Não remova proteções, aprovação, sandbox, testes ou rollback.",
                "Prefira modificar um único arquivo.",
                "O conteúdo retornado deve ser o arquivo Python completo, não um diff.",
                "Não invente dependências externas se não forem necessárias."
            ]
        }

    def prompt(self, proposta):
        ctx = self.contexto_para_modelo(proposta)
        return """Você é o engenheiro interno da Ashley 1.0.
Analise a proposta e o código fornecido e produza UMA melhoria candidata pequena.
Responda SOMENTE JSON válido neste formato:
{
  "arquivo": "caminho/relativo.py",
  "explicacao": "o que mudou e por quê",
  "codigo_completo": "conteúdo completo do arquivo",
  "teste_sugerido": "descrição curta do teste"
}
Não use markdown. Não altere segurança, autenticação, credenciais, permissões,
banco de dados ou o próprio mecanismo de governança/autoevolução.

CONTEXTO:
""" + json.dumps(ctx, ensure_ascii=False)

    def interpretar_resposta(self, resposta):
        texto = str(resposta).strip()
        if texto.startswith("```"):
            texto = re.sub(r"^```(?:json)?\s*", "", texto)
            texto = re.sub(r"\s*```$", "", texto)
        obj = json.loads(texto)
        for k in ("arquivo", "explicacao", "codigo_completo"):
            if not obj.get(k):
                raise ValueError(f"Resposta V10 sem campo obrigatório: {k}")
        arquivo = str(obj["arquivo"]).replace("\\", "/")
        risco = self.self_coder.avaliar_risco([arquivo], obj.get("explicacao", ""))
        if risco in {"ALTO", "CRITICO"}:
            raise PermissionError(
                "A candidata atingiu componente protegido/alto risco e foi bloqueada."
            )
        return obj, risco

    def aplicar_e_testar(self, proposta, resposta_modelo, comandos=None):
        candidato, risco = self.interpretar_resposta(resposta_modelo)
        workspace = self.self_coder.criar_workspace(proposta["id"])
        aplicado = self.self_coder.aplicar_conteudo_candidato(
            workspace, candidato["arquivo"], candidato["codigo_completo"]
        )
        sintaxe = self.self_coder.validar_python(workspace)
        if sintaxe["ok"]:
            testes = self.self_coder.executar_testes(workspace, comandos=comandos)
        else:
            testes = {"ok": False, "resultados": []}

        diff = self.self_coder.diff(workspace, candidato["arquivo"])
        return {
            "ok": bool(sintaxe["ok"] and testes["ok"]),
            "proposta_id": proposta["id"],
            "workspace": str(workspace),
            "arquivo": candidato["arquivo"],
            "explicacao": candidato["explicacao"],
            "teste_sugerido": candidato.get("teste_sugerido"),
            "risco": risco,
            "aplicado_sandbox": aplicado,
            "sintaxe": sintaxe,
            "testes": testes,
            "diff": diff,
            "promovido": False
        }
