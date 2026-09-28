from typing import Any, Dict, List, Optional
from datetime import datetime


class PlannerAshley:
    """
    Agente responsável por transformar um objetivo em um plano
    operacional antes da execução.

    O Planner pode considerar experiências anteriores da Ashley,
    mas não executa ferramentas nem altera o sistema.
    """

    def __init__(self):
        self.nome = "PlannerAshley"
        self.versao = "1.0"

    def criar_plano(
        self,
        objetivo: str,
        experiencias: Optional[List[Dict[str, Any]]] = None,
        ferramentas_disponiveis: Optional[List[str]] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        experiencias = experiencias or []
        ferramentas_disponiveis = ferramentas_disponiveis or []
        contexto = contexto or {}

        objetivo_normalizado = objetivo.strip()
        objetivo_lower = objetivo_normalizado.lower()

        # -----------------------------------------
        # 1. IDENTIFICAR TIPO DE TAREFA
        # -----------------------------------------

        tipo_tarefa = self._identificar_tipo_tarefa(
            objetivo_lower
        )

        # -----------------------------------------
        # 2. ANALISAR EXPERIÊNCIAS ANTERIORES
        # -----------------------------------------

        aprendizados = self._extrair_aprendizados(
            experiencias
        )

        # -----------------------------------------
        # 3. DEFINIR NECESSIDADE DE FERRAMENTAS
        # -----------------------------------------

        ferramenta_sugerida = None

        if tipo_tarefa == "pesquisa_web":
            ferramenta_sugerida = self._localizar_ferramenta(
                ferramentas_disponiveis,
                ["web", "pesquisa", "search"]
            )

        # -----------------------------------------
        # 4. CONSTRUIR ETAPAS
        # -----------------------------------------

        etapas = [
            {
                "ordem": 1,
                "acao": "interpretar_objetivo",
                "descricao": "Compreender o objetivo solicitado."
            }
        ]

        if aprendizados:
            etapas.append({
                "ordem": len(etapas) + 1,
                "acao": "considerar_experiencias",
                "descricao":
                    "Considerar aprendizados relevantes "
                    "de execuções anteriores."
            })

        if ferramenta_sugerida:
            etapas.append({
                "ordem": len(etapas) + 1,
                "acao": "usar_ferramenta",
                "ferramenta": ferramenta_sugerida,
                "descricao":
                    f"Executar a ferramenta "
                    f"'{ferramenta_sugerida}'."
            })

        etapas.append({
            "ordem": len(etapas) + 1,
            "acao": "validar_resultado",
            "descricao":
                "Verificar se o resultado atende ao objetivo."
        })

        etapas.append({
            "ordem": len(etapas) + 1,
            "acao": "responder_usuario",
            "descricao":
                "Produzir a resposta final somente após validação."
        })

        # -----------------------------------------
        # 5. RETORNAR PLANO ESTRUTURADO
        # -----------------------------------------

        return {
            "planner": self.nome,
            "versao": self.versao,
            "criado_em": datetime.now().isoformat(),
            "objetivo": objetivo_normalizado,
            "tipo_tarefa": tipo_tarefa,

            "experiencias_consultadas": len(experiencias),
            "aprendizados_relevantes": aprendizados,

            "ferramentas_disponiveis":
                ferramentas_disponiveis,

            "ferramenta_sugerida":
                ferramenta_sugerida,

            "etapas": etapas,

            "status": "planejado"
        }
        
    def converter_experiencias_memoria(
        self,
        experiencias_brutas: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Converte as tuplas retornadas pela MemoriaEstrategica
        para o formato utilizado pelo PlannerAshley.
        """

        experiencias_convertidas = []

        for experiencia in experiencias_brutas:

            if not isinstance(experiencia, (list, tuple)):
                continue

            if len(experiencia) < 8:
                continue

            experiencias_convertidas.append({
                "objetivo": experiencia[0],
                "estrategia": experiencia[1],
                "resultado": experiencia[2],
                "sucesso": bool(experiencia[3]),
                "erro": experiencia[4],
                "licao": experiencia[5],
                "confianca": experiencia[6],
                "status": experiencia[7]
            })

        return experiencias_convertidas

    # =====================================================
    # MÉTODOS INTERNOS
    # =====================================================

    def _identificar_tipo_tarefa(
        self,
        texto: str
    ) -> str:

        termos_web = [
            "pesquise",
            "pesquisar",
            "procure na internet",
            "buscar na internet",
            "busque na internet",
            "notícias",
            "noticias",
            "atualizado",
            "atualizada",
            "hoje",
            "agora"
        ]

        if any(
            termo in texto
            for termo in termos_web
        ):
            return "pesquisa_web"

        termos_analise = [
            "analise",
            "analisar",
            "compare",
            "comparar",
            "avalie",
            "avaliar"
        ]

        if any(
            termo in texto
            for termo in termos_analise
        ):
            return "analise"

        termos_criacao = [
            "crie",
            "criar",
            "escreva",
            "elabore",
            "desenvolva",
            "gere"
        ]

        if any(
            termo in texto
            for termo in termos_criacao
        ):
            return "criacao"

        return "conversa"

    def _extrair_aprendizados(
        self,
        experiencias: List[Dict[str, Any]]
    ) -> List[str]:

        aprendizados = []

        for experiencia in experiencias:

            if not isinstance(experiencia, dict):
                continue

            licao = (
                experiencia.get("licao")
                or experiencia.get("licao_aprendida")
                or experiencia.get("aprendizado")
            )

            if (
                licao
                and licao not in aprendizados
            ):
                aprendizados.append(str(licao))

        return aprendizados[:5]

    def _localizar_ferramenta(
        self,
        ferramentas: List[str],
        termos: List[str]
    ) -> Optional[str]:

        for ferramenta in ferramentas:

            nome = str(ferramenta).lower()

            if any(
                termo in nome
                for termo in termos
            ):
                return ferramenta

        return None