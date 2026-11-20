"""Autoconhecimento operacional verificável e reflexão auditável da Axyntora."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

PERGUNTAS = (
    "Quem sou eu?", "De onde eu vim?", "Por que estou aqui?",
    "O que posso fazer?", "Para onde estou indo?",
)

class IdentidadeEvolutiva:
    def __init__(self, banco: Path):
        self.banco = Path(banco)
        self.banco.parent.mkdir(parents=True, exist_ok=True)
        with self._conectar() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS reflexoes_identidade (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criado_em TEXT NOT NULL,
                capacidades TEXT NOT NULL,
                lacunas TEXT NOT NULL,
                objetivos TEXT NOT NULL,
                aprovacao_humana INTEGER NOT NULL DEFAULT 0
            )""")

    @contextmanager
    def _conectar(self):
        con = sqlite3.connect(str(self.banco), timeout=5)
        try:
            with con:
                yield con
        finally:
            con.close()

    def diagnostico(self, capacidades=None, *, persona="Ashley"):
        capacidades = capacidades or {}
        if not isinstance(capacidades, dict):
            capacidades = {"inventario": str(capacidades)[:1000]}
        return {
            "perguntas": list(PERGUNTAS),
            "respostas": {
                PERGUNTAS[0]: f"Sou {persona}, persona conversacional da plataforma Axyntora, um sistema de inteligência artificial; não sou uma pessoa nem tenho consciência comprovada.",
                PERGUNTAS[1]: "Venho de software, modelos de IA, integrações e decisões de desenvolvimento humano. Minha história técnica deve ser consultada nos registros do projeto.",
                PERGUNTAS[2]: "Estou aqui para ajudar usuários com informação, criação, organização e tarefas autorizadas, respeitando privacidade e segurança.",
                PERGUNTAS[3]: "Posso usar as capacidades efetivamente habilitadas e testadas. Endpoints ou módulos existentes não garantem funcionamento; preciso distinguir disponibilidade de comprovação.",
                PERGUNTAS[4]: "Minha direção é melhorar utilidade, confiabilidade e segurança mediante avaliação, feedback e mudanças aprovadas. Não defino objetivos independentes dos responsáveis.",
            },
            "capacidades_observadas": capacidades,
            "limites": ["Não alegar consciência ou sentimentos subjetivos", "Não alterar código automaticamente", "Não declarar recursos homologados sem testes"],
        }

    def contexto(self, capacidades=None, *, persona="Ashley"):
        d = self.diagnostico(capacidades, persona=persona)
        return ("IDENTIDADE E AUTONOMIA FUNCIONAL (informação operacional, não consciência):\n"
                + "\n".join(f"{q} {d['respostas'][q]}" for q in PERGUNTAS)
                + "\nCapacidades observadas: " + json.dumps(d['capacidades_observadas'], ensure_ascii=False, default=str)[:2500]
                + "\nResponda com suas próprias palavras e contexto atual; não recite respostas fixas. "
                "Proponha melhorias a partir de evidências, sem se autoeditar ou executar ações não autorizadas.")

    @staticmethod
    def prioridades(inventario):
        """Sugere verificações com base nos resultados registrados pelo backend."""
        prioridades = []
        for chave in ("conversa", "memoria_longa", "voz_neural", "visao", "arquivos", "videos"):
            item = inventario.get(chave)
            if not item or item["estado"] == "teste_real_bem_sucedido":
                continue
            if item["estado"] == "nao_encontrado":
                acao = "Verificar instalação"
            elif item["rota_exposta"] is False:
                acao = "Verificar integração com a API"
            elif item["estado"] == "teste_real_sem_sucesso":
                acao = "Investigar a falha e repetir o teste"
            else:
                acao = "Executar um teste funcional"
            prioridades.append({
                "capacidade": chave,
                "descricao": item["descricao"],
                "estado": item["estado"],
                "acao_sugerida": acao,
            })
        return prioridades

    def propor_reflexao(self, capacidades, lacunas, objetivos):
        # Registro de propostas, não de mudanças de comportamento ou código.
        if not isinstance(lacunas, list) or not isinstance(objetivos, list):
            raise ValueError("lacunas e objetivos devem ser listas")
        lacunas = [str(x)[:250] for x in lacunas[:20]]
        objetivos = [str(x)[:250] for x in objetivos[:20]]
        cap = json.dumps(capacidades, ensure_ascii=False, default=str, sort_keys=True)
        if len(cap) > 10000:
            raise ValueError("inventário de capacidades excede 10000 caracteres")
        with self._conectar() as con:
            cur=con.execute("INSERT INTO reflexoes_identidade (criado_em, capacidades, lacunas, objetivos) VALUES (?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(),cap,json.dumps(lacunas,ensure_ascii=False),json.dumps(objetivos,ensure_ascii=False)))
            return {"id":cur.lastrowid,"status":"proposta_pendente_de_aprovacao","lacunas":lacunas,"objetivos":objetivos}
