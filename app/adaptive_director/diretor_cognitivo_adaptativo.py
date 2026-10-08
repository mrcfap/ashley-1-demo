"""
ASHLEY 1.0 — V21
Diretor Cognitivo Adaptativo por Consequência

Responsabilidades:
- decompor objetivos complexos em especialistas temporários;
- decidir dependências e ordem de execução;
- registrar resultados esperados;
- receber resultados observados;
- comparar previsto x ocorrido;
- extrair lições com confiança explícita;
- reutilizar experiências sem transformar um caso isolado em regra universal.

O V21 NÃO concede novas permissões, NÃO executa ações externas por conta própria
e NÃO altera o próprio código. Orquestrador, Critic e Governança continuam sendo
as camadas responsáveis por validação e autorização.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _texto(valor: Any, limite: int = 12000) -> str:
    if isinstance(valor, str):
        return valor[:limite]
    return json.dumps(valor, ensure_ascii=False, default=str)[:limite]


@dataclass
class EspecialistaTemporario:
    id: str
    nome: str
    perfil: str
    tarefa: str
    depende_de: List[str] = field(default_factory=list)
    criterio_sucesso: str = ""
    resultado_esperado: str = ""
    status: str = "PLANEJADO"
    resultado: Optional[str] = None


@dataclass
class PlanoAdaptativo:
    ciclo_id: str
    objetivo: str
    estrategia: str
    especialistas: List[EspecialistaTemporario]
    resultado_esperado_geral: str
    criado_em: str = field(default_factory=_agora)


class MemoriaConsequenciasV21:
    def __init__(self, db_path: str = "data/ashley_v21.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def _conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ciclos_v21 (
                    ciclo_id TEXT PRIMARY KEY,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    objetivo TEXT NOT NULL,
                    plano_json TEXT NOT NULL,
                    resultado_esperado TEXT,
                    resultado_observado TEXT,
                    diferenca TEXT,
                    efeitos_inesperados TEXT,
                    licao TEXT,
                    confianca REAL,
                    quando_reutilizar TEXT,
                    quando_nao_reutilizar TEXT,
                    status TEXT NOT NULL
                )
            """)
            conn.commit()

    def registrar_plano(self, plano: PlanoAdaptativo):
        agora = _agora()
        with self._conectar() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ciclos_v21 (
                    ciclo_id, criado_em, atualizado_em, objetivo, plano_json,
                    resultado_esperado, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                plano.ciclo_id,
                plano.criado_em,
                agora,
                plano.objetivo,
                json.dumps(asdict(plano), ensure_ascii=False),
                plano.resultado_esperado_geral,
                "PLANEJADO"
            ))
            conn.commit()

    def concluir(
        self,
        ciclo_id: str,
        resultado_observado: str,
        diferenca: str,
        efeitos_inesperados: str,
        licao: str,
        confianca: float,
        quando_reutilizar: str,
        quando_nao_reutilizar: str,
    ):
        with self._conectar() as conn:
            conn.execute("""
                UPDATE ciclos_v21
                SET atualizado_em=?, resultado_observado=?, diferenca=?,
                    efeitos_inesperados=?, licao=?, confianca=?,
                    quando_reutilizar=?, quando_nao_reutilizar=?, status=?
                WHERE ciclo_id=?
            """, (
                _agora(), resultado_observado, diferenca, efeitos_inesperados,
                licao, max(0.0, min(1.0, float(confianca))),
                quando_reutilizar, quando_nao_reutilizar,
                "OBSERVADO", ciclo_id
            ))
            conn.commit()

    def obter(self, ciclo_id: str) -> Optional[Dict[str, Any]]:
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT * FROM ciclos_v21 WHERE ciclo_id=?",
                (ciclo_id,)
            ).fetchone()
        return dict(row) if row else None

    def experiencias_recentes(self, limite: int = 5) -> List[Dict[str, Any]]:
        with self._conectar() as conn:
            rows = conn.execute("""
                SELECT ciclo_id, objetivo, resultado_esperado,
                       resultado_observado, licao, confianca,
                       quando_reutilizar, quando_nao_reutilizar, status
                FROM ciclos_v21
                WHERE status='OBSERVADO'
                ORDER BY atualizado_em DESC
                LIMIT ?
            """, (max(1, int(limite)),)).fetchall()
        return [dict(r) for r in rows]


class DiretorCognitivoAdaptativoConsequencia:
    """
    V21: coordena planejamento adaptativo + aprendizagem por consequência.

    O Gemini é usado para raciocínio estruturado. A execução de ferramentas,
    ações externas e alterações estruturais permanece fora deste motor.
    """

    VERSAO = "V21.2-ConsequenciaFallback"

    def __init__(
        self,
        gemini_service=None,
        db_path: str = "data/ashley_v21.db",
        max_especialistas: int = 6,
    ):
        self.gemini = gemini_service
        self.memoria = MemoriaConsequenciasV21(db_path)
        self.max_especialistas = max(1, min(int(max_especialistas), 8))

    def status(self) -> Dict[str, Any]:
        return {
            "motor": "Diretor Cognitivo Adaptativo por Consequência",
            "versao": self.VERSAO,
            "ativo": True,
            "gemini_disponivel": self.gemini is not None,
            "max_especialistas": self.max_especialistas,
            "capacidades": [
                "planejamento_adaptativo",
                "especialistas_temporarios",
                "dependencias",
                "previsao_de_resultado",
                "aprendizagem_por_consequencia",
                "memoria_de_licoes",
                "fallback_local_deterministico",
            ],
            "limites": [
                "nao_concede_permissoes",
                "nao_executa_acoes_externas_sozinho",
                "nao_altera_o_proprio_codigo",
                "licoes_nao_sao_regras_universais",
            ],
        }

    async def _chat_json(self, system: str, message: str) -> Dict[str, Any]:
        if self.gemini is None:
            raise RuntimeError("GeminiService não foi fornecido ao V21.")

        resposta = await self.gemini.chat_com_fallback(
            system=system,
            message=message,
            history=[]
        )
        bruto = resposta if isinstance(resposta, str) else _texto(resposta)

        # Aceita JSON puro ou JSON cercado por markdown.
        bruto = bruto.strip()
        if bruto.startswith("```"):
            linhas = bruto.splitlines()
            if linhas:
                linhas = linhas[1:]
            if linhas and linhas[-1].strip().startswith("```"):
                linhas = linhas[:-1]
            bruto = "\n".join(linhas).strip()
            if bruto.lower().startswith("json"):
                bruto = bruto[4:].lstrip()

        try:
            dados = json.loads(bruto)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"V21 recebeu resposta não estruturada do modelo: {exc}"
            ) from exc

        # Alguns provedores/wrappers podem devolver um array JSON mesmo quando
        # o prompt pede um objeto. Normalizamos formatos seguros antes de o
        # restante do V21 usar .get().
        if isinstance(dados, list):
            if len(dados) == 1 and isinstance(dados[0], dict):
                dados = dados[0]
            elif dados and all(isinstance(item, dict) for item in dados):
                # Se a lista parecer ser diretamente a lista de especialistas,
                # preserva-a no esquema esperado pelo V21.
                dados = {"especialistas": dados}
            else:
                raise ValueError(
                    "V21 recebeu JSON em lista incompatível com o planejamento esperado."
                )

        if not isinstance(dados, dict):
            raise ValueError(
                f"V21 esperava objeto JSON, mas recebeu {type(dados).__name__}."
            )

        return dados

    def _normalizar_plano(
        self,
        objetivo: str,
        dados: Dict[str, Any]
    ) -> PlanoAdaptativo:
        itens = dados.get("especialistas") or dados.get("subtarefas") or []
        especialistas: List[EspecialistaTemporario] = []

        if isinstance(itens, dict):
            itens = [itens]
        if not isinstance(itens, list):
            itens = []

        for indice, item in enumerate(itens[: self.max_especialistas], start=1):
            if not isinstance(item, dict):
                continue
            esp_id = str(item.get("id") or f"E{indice}")
            especialistas.append(
                EspecialistaTemporario(
                    id=esp_id,
                    nome=str(item.get("nome") or item.get("nome_agente") or f"Especialista {indice}"),
                    perfil=str(item.get("perfil") or item.get("perfil_agente") or ""),
                    tarefa=str(item.get("tarefa") or item.get("instrucao_tarefa") or ""),
                    depende_de=[str(x) for x in (item.get("depende_de") or [])],
                    criterio_sucesso=str(item.get("criterio_sucesso") or ""),
                    resultado_esperado=str(item.get("resultado_esperado") or ""),
                )
            )

        if not especialistas:
            raise ValueError("O planejamento V21 não produziu especialistas válidos.")

        return PlanoAdaptativo(
            ciclo_id=str(uuid.uuid4()),
            objetivo=objetivo,
            estrategia=str(
                dados.get("estrategia")
                or dados.get("plano_geral")
                or "Estratégia adaptativa não descrita."
            ),
            especialistas=especialistas,
            resultado_esperado_geral=str(
                dados.get("resultado_esperado_geral")
                or dados.get("resultado_esperado")
                or "Resultado esperado ainda não especificado."
            ),
        )

    def _plano_fallback_local(
        self,
        objetivo: str,
        contexto: Optional[Dict[str, Any]] = None,
        motivo: str = "",
    ) -> Dict[str, Any]:
        """
        Planejamento determinístico de contingência.
        Não usa LLM, não executa ferramentas e não concede permissões.
        """
        objetivo_limpo = (objetivo or "").strip()
        contexto = contexto or {}

        dados = {
            "estrategia": (
                "Plano local de contingência em três etapas: analisar o objetivo, "
                "estruturar uma proposta e validar coerência/limites antes de qualquer execução."
            ),
            "resultado_esperado_geral": (
                f"Produzir um plano estruturado e validável para: {objetivo_limpo}"
            ),
            "especialistas": [
                {
                    "id": "E1",
                    "nome": "Analista de Objetivo",
                    "perfil": "análise e decomposição",
                    "tarefa": (
                        f"Analisar o objetivo, restrições, contexto disponível e critérios "
                        f"de sucesso: {objetivo_limpo}"
                    ),
                    "depende_de": [],
                    "criterio_sucesso": "Objetivo decomposto com premissas, restrições e lacunas explícitas.",
                    "resultado_esperado": "Mapa claro do problema e dos requisitos."
                },
                {
                    "id": "E2",
                    "nome": "Estrategista de Solução",
                    "perfil": "síntese e planejamento",
                    "tarefa": (
                        "Construir uma estratégia prática usando somente o objetivo, "
                        "o contexto autorizado e a análise produzida pelo E1."
                    ),
                    "depende_de": ["E1"],
                    "criterio_sucesso": "Estratégia coerente, executável e sem alegar ações não realizadas.",
                    "resultado_esperado": "Plano de ação estruturado com resultado esperado."
                },
                {
                    "id": "E3",
                    "nome": "Validador de Coerência",
                    "perfil": "crítica, plausibilidade e governança",
                    "tarefa": (
                        "Revisar o plano, identificar riscos, inconsistências, dependências "
                        "não atendidas e pontos que exigem autorização humana."
                    ),
                    "depende_de": ["E1", "E2"],
                    "criterio_sucesso": "Plano revisado com limites, riscos e pendências explícitos.",
                    "resultado_esperado": "Plano pronto para validação pelo Orquestrador/Critic/Governança."
                }
            ][: self.max_especialistas],
        }

        plano = self._normalizar_plano(objetivo_limpo, dados)
        self.memoria.registrar_plano(plano)

        return {
            "v21_ativo": True,
            "fase": "PLANEJAMENTO",
            "modo": "FALLBACK_LOCAL",
            "provedor_externo_usado": False,
            "motivo_fallback": _texto(motivo, limite=1500),
            "plano": asdict(plano),
            "regra": (
                "Plano determinístico de contingência. Não representa resposta do Gemini, "
                "não autoriza ações externas e não amplia permissões."
            ),
        }

    async def planejar(
        self,
        objetivo: str,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        objetivo = (objetivo or "").strip()
        if not objetivo:
            raise ValueError("Objetivo do V21 não pode ser vazio.")

        experiencias = self.memoria.experiencias_recentes(limite=5)
        system = f"""
Você é o V21 — Diretor Cognitivo Adaptativo por Consequência da Ashley.
Planeje, não execute ações externas.

Decida quantos especialistas temporários são realmente necessários, de 1 a
{self.max_especialistas}. Não crie especialistas redundantes. Declare
dependências. Um especialista é um papel temporário, não um novo modelo
treinado e não recebe novas permissões.

Use experiências anteriores apenas como evidência contextual. Um sucesso
passado não prova que a mesma estratégia funcionará novamente.

Responda SOMENTE JSON válido:
{{
  "estrategia": "...",
  "resultado_esperado_geral": "...",
  "especialistas": [
    {{
      "id": "E1",
      "nome": "...",
      "perfil": "...",
      "tarefa": "...",
      "depende_de": [],
      "criterio_sucesso": "...",
      "resultado_esperado": "..."
    }}
  ]
}}
""".strip()

        message = (
            f"OBJETIVO:\n{objetivo}\n\n"
            f"CONTEXTO:\n{_texto(contexto or {})}\n\n"
            f"EXPERIÊNCIAS ANTERIORES:\n{_texto(experiencias)}"
        )
        try:
            dados = await self._chat_json(system, message)
            plano = self._normalizar_plano(objetivo, dados)
            self.memoria.registrar_plano(plano)

            return {
                "v21_ativo": True,
                "fase": "PLANEJAMENTO",
                "modo": "GEMINI",
                "provedor_externo_usado": True,
                "plano": asdict(plano),
                "regra": (
                    "O plano define especialistas temporários; não autoriza ações "
                    "externas nem amplia permissões."
                ),
            }
        except Exception as exc:
            # Resiliência do V21: indisponibilidade, quota/rate limit, erro HTTP,
            # resposta inválida ou falha do provedor não derrubam o planejamento.
            # O fallback é explicitamente identificado e não finge ser Gemini.
            return self._plano_fallback_local(
                objetivo=objetivo,
                contexto=contexto,
                motivo=f"{type(exc).__name__}: {exc}",
            )

    def proximos_especialistas(
        self,
        plano: Dict[str, Any],
        concluidos: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        concluidos_set = set(concluidos or [])
        prontos = []
        for esp in plano.get("especialistas", []):
            if esp.get("id") in concluidos_set:
                continue
            deps = set(esp.get("depende_de") or [])
            if deps.issubset(concluidos_set):
                prontos.append(esp)
        return prontos

    async def executar_especialista(
        self,
        especialista: Dict[str, Any],
        objetivo: str,
        contexto_acumulado: Any = None,
    ) -> Dict[str, Any]:
        """
        Executa somente raciocínio textual do especialista via Gemini.
        Ferramentas externas continuam sob controle do Orquestrador/Governança.
        """
        system = f"""
Você é um especialista temporário criado pelo V21 da Ashley.

NOME: {especialista.get("nome", "Especialista")}
PERFIL: {especialista.get("perfil", "")}

Resolva apenas a tarefa atribuída. Não invente que executou ferramentas,
pesquisas, pagamentos, alterações de arquivos ou ações externas que não foram
realmente fornecidas. Declare incertezas e dependências.
""".strip()

        message = (
            f"OBJETIVO GERAL:\n{objetivo}\n\n"
            f"TAREFA:\n{especialista.get('tarefa', '')}\n\n"
            f"CRITÉRIO DE SUCESSO:\n{especialista.get('criterio_sucesso', '')}\n\n"
            f"CONTEXTO ACUMULADO:\n{_texto(contexto_acumulado or {})}"
        )
        if self.gemini is None:
            raise RuntimeError("GeminiService não foi fornecido ao V21.")

        resultado = await self.gemini.chat_com_fallback(
            system=system,
            message=message,
            history=[]
        )
        return {
            "especialista_id": especialista.get("id"),
            "nome": especialista.get("nome"),
            "resultado": resultado,
            "status": "CONCLUIDO",
            "requer_validacao": True,
        }

    async def analisar_consequencia(
        self,
        ciclo_id: str,
        resultado_observado: Any,
        efeitos_inesperados: Optional[Any] = None,
    ) -> Dict[str, Any]:
        registro = self.memoria.obter(ciclo_id)
        if not registro:
            raise ValueError(f"Ciclo V21 não encontrado: {ciclo_id}")

        system = """
Você é a camada de aprendizagem por consequência do V21 da Ashley.
Compare previsão e resultado observado sem racionalizar o erro.

Extraia uma lição proporcional à evidência. Um único caso deve produzir
confiança limitada. Diferencie falha da estratégia, falha de execução,
mudança de contexto e ausência de evidência.

Responda SOMENTE JSON válido:
{
  "diferenca": "...",
  "efeitos_inesperados": "...",
  "licao": "...",
  "confianca": 0.0,
  "quando_reutilizar": "...",
  "quando_nao_reutilizar": "..."
}
""".strip()

        message = (
            f"OBJETIVO:\n{registro['objetivo']}\n\n"
            f"RESULTADO ESPERADO:\n{registro.get('resultado_esperado') or ''}\n\n"
            f"RESULTADO OBSERVADO:\n{_texto(resultado_observado)}\n\n"
            f"EFEITOS INESPERADOS INFORMADOS:\n{_texto(efeitos_inesperados or '')}"
        )
        modo = "GEMINI"
        provedor_externo_usado = True
        motivo_fallback = ""

        try:
            dados = await self._chat_json(system, message)
        except Exception as exc:
            # Fallback factual e conservador: registra somente o que é sustentado
            # pelo resultado observado. Não inventa causalidade, eficácia externa
            # ou uma lição forte quando o provedor cognitivo está indisponível.
            modo = "FALLBACK_LOCAL"
            provedor_externo_usado = False
            motivo_fallback = f"{type(exc).__name__}: {exc}"

            observado_txt = _texto(resultado_observado)
            esperado_txt = str(registro.get("resultado_esperado") or "")
            efeitos_txt = _texto(efeitos_inesperados or "")

            marcador_teste = "teste" in observado_txt.lower()
            marcador_nao_ocorreu = any(
                termo in observado_txt.lower()
                for termo in (
                    "não ocorreu",
                    "nao ocorreu",
                    "ainda não ocorreu",
                    "ainda nao ocorreu",
                    "não foi execut",
                    "nao foi execut",
                )
            )

            if marcador_teste or marcador_nao_ocorreu:
                diferenca = (
                    "O resultado observado descreve uma avaliação/teste controlado, "
                    "não a ocorrência do resultado externo esperado. A eficácia real "
                    "permanece não observada."
                )
                licao = (
                    "Há evidência apenas de que a estrutura pôde ser avaliada no "
                    "contexto informado. Não há evidência suficiente para concluir "
                    "que a estratégia produzirá o resultado externo esperado."
                )
                quando_reutilizar = (
                    "Como referência de estruturação e validação preliminar em "
                    "contextos semelhantes, mantendo nova validação."
                )
                quando_nao_reutilizar = (
                    "Não usar este registro como prova de eficácia externa, sucesso "
                    "com investidores ou validação de resultado que ainda não ocorreu."
                )
                confianca_fallback = 0.20
            else:
                diferenca = (
                    f"Esperado registrado: {esperado_txt[:700]}. "
                    "Observado foi persistido, mas a comparação semântica aprofundada "
                    "não pôde ser realizada sem o provedor cognitivo."
                )
                licao = (
                    "Resultado observado registrado para revisão posterior. "
                    "Sem análise do provedor, nenhuma conclusão causal ou generalização "
                    "forte deve ser inferida."
                )
                quando_reutilizar = (
                    "Somente como evidência contextual bruta em situação semelhante, "
                    "sujeita a nova validação."
                )
                quando_nao_reutilizar = (
                    "Não reutilizar como regra universal, prova causal ou garantia "
                    "de repetição do resultado."
                )
                confianca_fallback = 0.15

            dados = {
                "diferenca": diferenca,
                "efeitos_inesperados": efeitos_txt,
                "licao": licao,
                "confianca": confianca_fallback,
                "quando_reutilizar": quando_reutilizar,
                "quando_nao_reutilizar": quando_nao_reutilizar,
            }

        confianca = dados.get("confianca", 0.25)
        try:
            confianca = float(confianca)
        except (TypeError, ValueError):
            confianca = 0.25
        confianca = max(0.0, min(1.0, confianca))

        # Uma única observação não deve virar certeza alta automaticamente.
        confianca = min(confianca, 0.70)

        self.memoria.concluir(
            ciclo_id=ciclo_id,
            resultado_observado=_texto(resultado_observado),
            diferenca=str(dados.get("diferenca") or ""),
            efeitos_inesperados=str(dados.get("efeitos_inesperados") or ""),
            licao=str(dados.get("licao") or ""),
            confianca=confianca,
            quando_reutilizar=str(dados.get("quando_reutilizar") or ""),
            quando_nao_reutilizar=str(dados.get("quando_nao_reutilizar") or ""),
        )

        return {
            "v21_ativo": True,
            "fase": "APRENDIZAGEM_POR_CONSEQUENCIA",
            "modo": modo,
            "provedor_externo_usado": provedor_externo_usado,
            "motivo_fallback": _texto(motivo_fallback, limite=1500) if motivo_fallback else "",
            "ciclo_id": ciclo_id,
            "resultado_esperado": registro.get("resultado_esperado"),
            "resultado_observado": _texto(resultado_observado),
            "diferenca": str(dados.get("diferenca") or ""),
            "efeitos_inesperados": str(dados.get("efeitos_inesperados") or ""),
            "licao": str(dados.get("licao") or ""),
            "confianca": confianca,
            "quando_reutilizar": str(dados.get("quando_reutilizar") or ""),
            "quando_nao_reutilizar": str(dados.get("quando_nao_reutilizar") or ""),
            "persistido": True,
            "regra": (
                "A lição é evidência contextual e revisável; não se torna "
                "automaticamente uma regra universal. Em FALLBACK_LOCAL, nenhuma "
                "eficácia externa ou causalidade não observada é inferida."
            ),
        }

    def registrar_consequencia_sem_modelo(
        self,
        ciclo_id: str,
        resultado_observado: str,
        diferenca: str,
        licao: str,
        confianca: float = 0.25,
        efeitos_inesperados: str = "",
        quando_reutilizar: str = "",
        quando_nao_reutilizar: str = "",
    ) -> Dict[str, Any]:
        """
        Caminho determinístico para testes ou consequências já avaliadas por
        outra camada. Não chama Gemini.
        """
        registro = self.memoria.obter(ciclo_id)
        if not registro:
            raise ValueError(f"Ciclo V21 não encontrado: {ciclo_id}")

        confianca = max(0.0, min(0.70, float(confianca)))
        self.memoria.concluir(
            ciclo_id,
            resultado_observado,
            diferenca,
            efeitos_inesperados,
            licao,
            confianca,
            quando_reutilizar,
            quando_nao_reutilizar,
        )
        return {
            "v21_ativo": True,
            "fase": "APRENDIZAGEM_POR_CONSEQUENCIA",
            "ciclo_id": ciclo_id,
            "licao": licao,
            "confianca": confianca,
            "persistido": True,
        }
