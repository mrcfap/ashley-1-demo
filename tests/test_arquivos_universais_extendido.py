from pathlib import Path
import zipfile
from app.services.arquivos_universais import extract_any


def test_markdown(tmp_path):
    p=tmp_path/'capitulo.md';p.write_text('# Capítulo\nTexto da obra',encoding='utf8')
    assert 'Texto da obra' in extract_any(p)


def test_html_removes_scripts(tmp_path):
    p=tmp_path/'livro.html';p.write_text('<h1>Capítulo</h1><script>perigo()</script><p>Texto</p>',encoding='utf8')
    result=extract_any(p)
    assert 'Capítulo' in result and 'Texto' in result and 'perigo()' not in result


def test_zip_reads_text_without_extracting(tmp_path):
    p=tmp_path/'livro.zip'
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('capitulo.txt','Conteúdo importante da obra')
        z.writestr('../nao_extrair.py','print("não executar")')
    assert 'Conteúdo importante da obra' in extract_any(p)
    assert not (tmp_path/'nao_extrair.py').exists()


def test_unknown_binary_is_honest(tmp_path):
    p=tmp_path/'desconhecido.abc';p.write_bytes(b'\x00\x01\x02')
    assert 'Não afirmar que o conteúdo foi analisado' in extract_any(p)


def test_epub_extracts_chapter(tmp_path):
    p=tmp_path/'livro.epub'
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('OEBPS/chapter1.xhtml','<html><body><h1>Primeiro capítulo</h1><p>Conteúdo do romance</p></body></html>')
    assert 'Conteúdo do romance' in extract_any(p)
