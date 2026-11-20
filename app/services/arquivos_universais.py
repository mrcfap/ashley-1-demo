"""Leitura local segura de arquivos para a Ashley.

Extrai conteúdo, não executa macros, scripts, anexos ou arquivos compactados.
Formatos não suportados são identificados explicitamente como metadados.
"""
from pathlib import Path
import csv
import io
import json
import mimetypes
import zipfile
import re

MAX_EXTRACT = 80000
MAX_TEXT_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100
TEXT = {'.txt','.md','.py','.js','.ts','.html','.htm','.css','.json','.jsonl','.xml','.yaml','.yml','.ini','.toml','.log','.sql','.sh','.ps1','.bat','.csv','.tsv','.rtf','.java','.c','.cpp','.h','.go','.rs','.php','.rb','.svg','.tex','.rst','.srt','.vtt','.ipynb'}


def _decode(raw):
    if b'\x00' in raw[:2048]:
        return None
    for encoding in ('utf-8-sig', 'utf-16', 'cp1252'):
        try:
            return raw.decode(encoding)
        except UnicodeError:
            pass
    return raw.decode('utf-8', errors='replace')


def _clean_html(value):
    from html import unescape
    value = re.sub(r'(?is)<(script|style)\b[^>]*>.*?</\1>', ' ', value)
    value = re.sub(r'(?s)<[^>]+>', ' ', value)
    return unescape(re.sub(r'\s+', ' ', value)).strip()


def _text_file(path):
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise ValueError('Arquivo textual excede 4 MB para extração local.')
    text = _decode(path.read_bytes())
    if text is None:
        return _metadata(path, 'Arquivo com bytes binários; não interpretado como texto.')
    if path.suffix.lower() in {'.html', '.htm'}:
        text = _clean_html(text)
    elif path.suffix.lower() == '.ipynb':
        try:
            nb = json.loads(text)
            text = '\n'.join(''.join(c.get('source', [])) for c in nb.get('cells', []))
        except (ValueError, TypeError):
            pass
    return text[:MAX_EXTRACT]


def _metadata(path, reason='Conteúdo não extraído automaticamente.'):
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return (f'Arquivo binário recebido: {path.name}; tipo provável: {mime}; '
            f'tamanho: {path.stat().st_size} bytes. {reason} '
            'Não afirmar que o conteúdo foi analisado.')


def _archive(path):
    lines = ['Arquivo compactado (somente leitura, sem executar conteúdo):']
    total = 0
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        for info in infos[:MAX_ARCHIVE_ENTRIES]:
            name = info.filename
            lines.append(f'ITEM: {name} ({info.file_size} bytes)')
            if info.is_dir() or info.flag_bits & 0x1:
                continue
            suffix = Path(name).suffix.lower()
            if suffix not in TEXT or info.file_size > 512_000:
                continue
            if total + info.file_size > MAX_ARCHIVE_BYTES:
                lines.append('[limite de extração do arquivo compactado atingido]')
                break
            total += info.file_size
            with z.open(info) as stream:
                raw = stream.read(min(info.file_size, 512_000) + 1)
            if len(raw) > 512_000:
                continue
            content = _decode(raw)
            if content is None:
                continue
            if suffix in {'.html', '.htm'}:
                content = _clean_html(content)
            lines.append('CONTEUDO DE '+name+':\n'+content[:4000])
            if len('\n'.join(lines)) >= MAX_EXTRACT:
                break
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            lines.append(f'[mais {len(infos)-MAX_ARCHIVE_ENTRIES} itens não examinados]')
    return '\n'.join(lines)[:MAX_EXTRACT]


def _epub(path):
    from html import unescape
    lines = ['Livro EPUB:']
    with zipfile.ZipFile(path) as z:
        for info in z.infolist()[:500]:
            if Path(info.filename).suffix.lower() not in {'.xhtml', '.html', '.htm'}:
                continue
            if info.file_size > 2_000_000 or info.flag_bits & 0x1:
                continue
            raw = z.read(info)
            text = _decode(raw)
            if text:
                lines.append('CAPITULO/ARQUIVO: '+info.filename+'\n'+_clean_html(text))
            if sum(map(len, lines)) >= MAX_EXTRACT:
                break
    return '\n'.join(lines)[:MAX_EXTRACT]


def extract_any(path):
    path = Path(path)
    ext = path.suffix.lower()
    if ext in {'.pdf', '.docx'}:
        from app.services.documentos import extract_text
        return extract_text(path)[:MAX_EXTRACT]
    if ext in TEXT:
        return _text_file(path)
    if ext == '.epub':
        return _epub(path)
    if ext == '.xlsx':
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        lines = []
        try:
            for sheet in wb:
                lines.append('ABA: '+sheet.title)
                for i, row in enumerate(sheet.iter_rows(values_only=True)):
                    if i >= 500: break
                    lines.append(' | '.join(str(v)[:200] if v is not None else '' for v in row[:30]))
                    if sum(map(len, lines)) > MAX_EXTRACT: break
        finally:
            wb.close()
        return '\n'.join(lines)[:MAX_EXTRACT]
    if ext == '.pptx':
        from pptx import Presentation
        prs = Presentation(str(path)); lines = []
        for i, slide in enumerate(prs.slides):
            lines.append('SLIDE '+str(i+1))
            for shape in slide.shapes:
                if shape.has_text_frame: lines.append(shape.text[:5000])
                if getattr(shape, 'has_table', False):
                    for row in shape.table.rows:
                        lines.append(' | '.join(cell.text[:300] for cell in row.cells))
            if sum(map(len, lines)) > MAX_EXTRACT: break
        return '\n'.join(lines)[:MAX_EXTRACT]
    if ext in {'.zip', '.cbz'}:
        return _archive(path)
    return _metadata(path)


def generate_extras(text, title, base):
    """Mantém a interface legada para exportação DOC/planilhas/apresentações."""
    from pptx import Presentation
    import xlsxwriter
    base = Path(base)
    base.parent.mkdir(parents=True, exist_ok=True)
    base.with_suffix('.txt').write_text(text, encoding='utf-8')
    base.with_suffix('.md').write_text('# '+title+'\n\n'+text, encoding='utf-8')
    sections = [x.strip() for x in text.split('\n\n') if x.strip()] or [text]
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = 'Gerado pela Ashley 1.0'
    for i in range(0, min(len(sections), 40), 4):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = f'{title[:55]} — {i//4+1}'
        slide.placeholders[1].text = '\n'.join('• '+v[:450] for v in sections[i:i+4])[:1800]
    prs.save(str(base.with_suffix('.pptx')))
    workbook = xlsxwriter.Workbook(str(base.with_suffix('.xlsx')), {"strings_to_formulas": False, "strings_to_urls": False})
    sheet = workbook.add_worksheet('Conteúdo')
    bold = workbook.add_format({'bold':True,'bg_color':'#E9F1FA'})
    sheet.write(0,0,'Título',bold); sheet.write(0,1,title)
    sheet.write(1,0,'Seção',bold); sheet.write(1,1,'Conteúdo',bold)
    for i, paragraph in enumerate(sections[:1000], start=2):
        sheet.write(i,0,i-1); sheet.write(i,1,paragraph[:32000])
    sheet.set_column(0,0,12); sheet.set_column(1,1,90)
    workbook.close()
    with base.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Seção','Conteúdo'])
        writer.writerows((i,x) for i,x in enumerate(sections[:1000],1))
