import json
import re
from typing import Any, Dict, List


class AnalisadorMemoriaAutomatica:
    """
    Analisa uma interação e decide, de forma conservadora,
    se alguma informação merece virar memória persistente.
    """

    CATEGORIAS_PERMITIDAS = {
        "projeto",
        "objetivo",
        "decisao",
        "preferencia",
        "pessoa",
        "regra",
        "restricao",
        "compromisso",
        "aprendizado",
    }

    def __init__(self, gemini_service, memoria_longa):
        self.gemini = gemini_service
        self.memoria = memoria_longa

    @staticmethod
    def _extrair_json(texto: str) -> Dict[str, Any]:
        """
        Aceita JSON puro ou JSON envolvido por ```json ... ```.
        """
        texto = (texto or "").strip()

        texto = re.sub(
            r"^```(?:json)?\s*",
            "",
            texto,
            flags=re.IGNORECASE,
        )
        texto = re.sub(r"\s*```$", "", texto).strip()

        try:
            return json.loads(texto)
        except Exception:
            inicio = texto.find("{")
            fim = texto.rfind("}")

            if inicio >= 0 and fim > inicio:
                return json.loads(texto[inicio: fim + 1])

            raise ValueError("Resposta do analisador não contém JSON válido.")

    @staticmethod
    def _normalizar_chave(chave: str) -> str:
        chave = (chave or "").strip().lower()
        chave = re.sub(r"\s+", "_", chave)
        chave = re.sub(r"[^a-z0-9_áéíóúâêôãõç-]", "", chave)
        return chave[:120]

    async def analisar(
        self,
        user_id: int,
        entrada: str,
        resposta: str,
    ) -> Dict[str, Any]:

        # Evita gastar uma chamada de modelo com mensagens muito pequenas.
        if len((entrada or "").strip()) < 12:
            return {
                "executado": False,
                "motivo": "entrada_curta",
                "memorias_salvas": 0,
            }

        system = """
Você é o módulo de seleção de memória persistente da Ashley 1.0.

Sua função NÃO é responder ao usuário.
Sua única função é decidir se a mensagem do usuário contém
informação realmente útil para interações futuras.

Seja conservador.

NÃO memorize:
- cumprimentos;
- conversa casual sem valor futuro;
- perguntas genéricas;
- informações temporárias sem importância;
- conteúdo inferido apenas pela resposta da IA;
- fatos que o usuário não afirmou;
- senhas, tokens, chaves de API ou outros segredos;
- números de cartão, documentos ou credenciais;
- conteúdo que não tenha utilidade futura clara.

PODE memorizar:
- informações estáveis sobre projetos;
- objetivos duradouros;
- decisões tomadas;
- preferências estáveis;
- pessoas ou relações relevantes mencionadas pelo usuário;
- regras e restrições;
- compromissos relevantes;
- aprendizados derivados de resultados concretos.

Categorias permitidas:
projeto, objetivo, decisao, preferencia, pessoa,
regra, restricao, compromisso, aprendizado.

Retorne SOMENTE JSON válido neste formato:

{
  "memorizar": true,
  "memorias": [
    {
      "categoria": "objetivo",
      "chave": "nome_curto_e_estavel",
      "conteudo": "informação objetiva que deverá ser lembrada",
      "importancia": 0.0,
      "permanencia": 0.0
    }
  ]
}

Se nada merecer memória:

{
  "memorizar": false,
  "memorias": []
}

Regras:
- no máximo 3 memórias por interação;
- importancia e permanencia devem ficar entre 0 e 1;
- só aceite memória com importância futura real;
- o conteúdo deve representar o que o USUÁRIO informou,
  e não uma invenção ou conclusão não confirmada da IA.
"""

        mensagem = f"""
MENSAGEM DO USUÁRIO:
{entrada[:12000]}

RESPOSTA DA ASHLEY:
{resposta[:12000]}
"""

        try:
            texto, modelo = await self.gemini.chat_com_fallback(
                system=system,
                message=mensagem,
                history=[],
            )

            dados = self._extrair_json(texto)

        except Exception as exc:
            # A memória automática nunca deve derrubar o chat.
            return {
                "executado": False,
                "motivo": "falha_analisador",
                "erro": f"{type(exc).__name__}: {exc}",
                "memorias_salvas": 0,
            }

        if not dados.get("memorizar"):
            return {
                "executado": True,
                "modelo": modelo,
                "memorias_salvas": 0,
                "motivo": "nenhuma_memoria_relevante",
            }

        candidatos: List[Dict[str, Any]] = dados.get("memorias") or []
        salvas = []

        for item in candidatos[:3]:
            if not isinstance(item, dict):
                continue

            categoria = str(item.get("categoria", "")).strip().lower()

            if categoria not in self.CATEGORIAS_PERMITIDAS:
                continue

            chave = self._normalizar_chave(str(item.get("chave", "")))
            conteudo = str(item.get("conteudo", "")).strip()

            if not chave or len(conteudo) < 5:
                continue

            try:
                importancia = float(item.get("importancia", 0.7))
            except (TypeError, ValueError):
                importancia = 0.7

            try:
                permanencia = float(item.get("permanencia", 0.8))
            except (TypeError, ValueError):
                permanencia = 0.8

            importancia = max(0.0, min(1.0, importancia))
            permanencia = max(0.0, min(1.0, permanencia))

            # Segunda barreira conservadora.
            if importancia < 0.65 or permanencia < 0.55:
                continue

            self.memoria.guardar(
                user_id=user_id,
                categoria=categoria,
                chave=chave,
                conteudo=conteudo[:12000],
                importancia=importancia,
                permanencia=permanencia,
            )

            salvas.append(
                {
                    "categoria": categoria,
                    "chave": chave,
                    "conteudo": conteudo[:12000],
                    "importancia": importancia,
                    "permanencia": permanencia,
                }
            )

        return {
            "executado": True,
            "modelo": modelo,
            "memorias_salvas": len(salvas),
            "memorias": salvas,
        }