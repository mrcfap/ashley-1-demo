"""V36-V38: simulations and change proposals; never autonomously deploy code."""
from pathlib import Path
import ast, hashlib, json, sqlite3, time, uuid

class TransitEngine:
    """V36. Explicit conditional scenarios, not predictions or parallel universes."""
    def simulate(self, decision: str, factors=None):
        factors=factors or {}
        scenarios=[]
        for name,benefit,risk,steps in [
            ('Alfa - conservador', 'Continuidade e reversibilidade', 'Mudanças graduais podem demorar', ['Criar backup','Alterar uma unidade','Executar testes de regressão']),
            ('Beta - experimental', 'Potencial de melhoria maior', 'Integrações novas podem falhar', ['Criar branch isolada','Medir benchmark antes/depois','Solicitar revisão humana']),
            ('Ômega - estresse', 'Identificação de pontos frágeis', 'Falhas simuladas não cobrem todas as falhas reais', ['Simular falha de rede','Simular concorrência e indisponibilidade','Verificar rollback'])]:
            scenarios.append({'nome':name,'beneficio_hipotetico':benefit,'risco_hipotetico':risk,'etapas_de_validacao':steps})
        return {'decisao':decision[:500], 'cenarios':scenarios, 'dados_observados':factors, 'escolha_automatica':False,'aviso':'Cenários hipotéticos; nenhum teste executado ou futuro previsto.'}

class GenesisEngine:
    """V37. Read-only AST audit and versioned change proposals. Never self-deploy."""
    def __init__(self, root): self.root=Path(root).resolve()
    def inspect(self, relative_path):
        target=(self.root/relative_path).resolve()
        if self.root not in target.parents or target.suffix!='.py' or not target.is_file():
            raise ValueError('Arquivo Python fora do workspace ou inexistente.')
        if any(part.startswith('.') or part in {'data','generated','uploads','__pycache__'} for part in target.relative_to(self.root).parts):
            raise ValueError('Caminho protegido.')
        source=target.read_text(encoding='utf-8'); tree=ast.parse(source)
        functions=[node.name for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
        return {'arquivo':str(target.relative_to(self.root)), 'sha256':hashlib.sha256(source.encode()).hexdigest(), 'linhas':len(source.splitlines()),'funcoes':functions[:100], 'alterado':False}
    def propose(self, relative_path, rationale):
        audit=self.inspect(relative_path)
        return {'id':uuid.uuid4().hex,'status':'PROPOSTA_NAO_APLICADA','diagnostico':audit,'justificativa':rationale[:1500], 'proximos_passos':['Revisão de código','Teste em sandbox isolado','Revisão de segurança','Aprovação humana explícita','Backup e rollback'], 'mutacao_executada':False}

class SentinelEngine:
    """V38. Safety gate and immutable-style SQLite decision audit."""
    def __init__(self,db):
        self.db=str(db)
        with sqlite3.connect(self.db) as c:
            c.execute('CREATE TABLE IF NOT EXISTS sentinel_events (id TEXT PRIMARY KEY, created INTEGER NOT NULL, category TEXT NOT NULL, summary TEXT NOT NULL, approved INTEGER NOT NULL DEFAULT 0)')
    def assess(self, category, description):
        high=category in {'deploy','self_modify','delete_data','credentials','external_action'}
        event={'id':uuid.uuid4().hex,'category':category,'summary':description[:500],'approval_required':high,'approved':False,'executed':False,'status':'REQUIRES_APPROVAL' if high else 'PROPOSAL_ONLY'}
        with sqlite3.connect(self.db) as c:
            c.execute('INSERT INTO sentinel_events (id,created,category,summary,approved) VALUES (?,?,?,?,0)',(event['id'],int(time.time()),category,description[:500]))
        return event
