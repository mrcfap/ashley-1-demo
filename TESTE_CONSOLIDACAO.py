"""Auditoria offline de módulos e geração de arquivos; não usa contas nem APIs externas."""
import ast
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
modules = set()
for source in (ROOT / 'app').rglob('*.py'):
    tree = ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('app.'):
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names if alias.name.startswith('app.'))
missing = [m for m in sorted(modules) if not (
    (ROOT / (m.replace('.', '/') + '.py')).is_file() or
    (ROOT / m.replace('.', '/') / '__init__.py').is_file()
)]
assert not missing, f'Módulos ausentes: {missing}'
print('OK: importações internas localizadas')

from app.advanced_v36_v38 import TransitEngine, GenesisEngine, SentinelEngine
from app.cognitive_v31_v35 import CognitiveV31V35
from app.future_engines import MotoresV27V30
print('OK: motores restaurados importáveis')

from app.services.arquivos_universais import extract_any, generate_extras
with tempfile.TemporaryDirectory() as folder:
    base = pathlib.Path(folder) / 'exemplo'
    generate_extras('Seção inicial\n\nSeção final', 'Documento de teste', base)
    for suffix in ['.pptx', '.xlsx', '.txt', '.md', '.csv']:
        path = base.with_suffix(suffix)
        assert path.is_file() and path.stat().st_size > 0, suffix
    assert 'Seção inicial' in extract_any(base.with_suffix('.txt'))
print('OK: extração textual e geração de 5 formatos')
print('Auditoria offline concluída; teste de servidor, autenticação e Gemini ainda necessário.')
