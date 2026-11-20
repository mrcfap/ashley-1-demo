"""V08/V09/V11: gera propostas de ferramentas; NUNCA executa código de IA na API.
Validação sintática não é teste de segurança. Execução deve ocorrer em sandbox de SO externo.
"""
import ast
import json
import re
from pathlib import Path
from uuid import uuid4

class MotorAutoEvolucaoV08:
    def __init__(self, ai_inference_service, proposal_dir):
        self.ai = ai_inference_service
        self.proposal_dir = Path(proposal_dir)

    async def propor_capacidade(self, demanda_usuario: str, nome_funcao: str):
        if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]{0,63}', nome_funcao):
            raise ValueError('Nome de função inválido')
        prompt = ('Gere uma proposta de função Python pura, sem efeitos colaterais, para: '
                  + demanda_usuario[:2000] + '\nNome: ' + nome_funcao
                  + '\nResponda JSON com codigo_fonte e codigo_teste. Não inclua segredos.')
        raw = await self.ai.gerar_texto(prompt)
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            raise ValueError('Formato inválido')
        source, tests = obj.get('codigo_fonte'), obj.get('codigo_teste')
        if not all(isinstance(x, str) and 0 < len(x) <= 20000 for x in (source, tests)):
            raise ValueError('Código ausente ou excessivo')
        ast.parse(source)
        ast.parse(tests)
        # Nenhum código gerado é importado ou executado no servidor principal.
        self.proposal_dir.mkdir(parents=True, exist_ok=True)
        uid = uuid4().hex
        folder = self.proposal_dir / uid
        folder.mkdir(mode=0o700)
        (folder / 'proposta.py.txt').write_text(source, encoding='utf8')
        (folder / 'teste.py.txt').write_text(tests, encoding='utf8')
        (folder / 'manifesto.json').write_text(json.dumps({
            'id': uid, 'funcao': nome_funcao, 'estado': 'AGUARDANDO_SANDBOX_E_APROVACAO',
            'executado': False, 'aplicado': False}, ensure_ascii=False), encoding='utf8')
        return {'id': uid, 'estado': 'AGUARDANDO_SANDBOX_E_APROVACAO', 'pasta': str(folder)}
