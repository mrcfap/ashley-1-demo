"""Memória visual privada: objetos no Supabase Storage, metadados no PostgreSQL."""
import os
import uuid
import json
import urllib.request
import urllib.error
from app.security.postgres import connect

BUCKET = 'axyntora-visual-private'
MIMES = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}


def _config():
    url = os.getenv('SUPABASE_URL', '').rstrip('/')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    if not url or not key or not os.getenv('DATABASE_URL'):
        raise RuntimeError('Memória visual indisponível: configure SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY e DATABASE_URL.')
    if not url.startswith('https://'):
        raise RuntimeError('SUPABASE_URL deve usar HTTPS.')
    return url, key


def _storage(method, path, payload=None, mime='application/json'):
    url, key = _config()
    req = urllib.request.Request(
        f'{url}/storage/v1/{path}', data=payload, method=method,
        headers={'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': mime},
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        raw = res.read()
        return json.loads(raw) if raw else {}


def save(user_id, name, description, raw, mime):
    name = name.strip()
    if not name or len(name) > 120 or len(description) > 3000:
        raise ValueError('Nome ou descrição inválidos.')
    if mime not in MIMES or not raw or len(raw) > 10 * 1024 * 1024:
        raise ValueError('Imagem inválida ou acima de 10 MB.')
    signatures = {'image/jpeg': raw.startswith(b'\xff\xd8\xff'), 'image/png': raw.startswith(b'\x89PNG\r\n\x1a\n'), 'image/webp': raw.startswith(b'RIFF') and raw[8:12] == b'WEBP'}
    if not signatures[mime]:
        raise ValueError('Conteúdo incompatível com o tipo da imagem.')
    item_id = str(uuid.uuid4())
    path = f'{int(user_id)}/{item_id}{MIMES[mime]}'
    _storage('POST', f'object/{BUCKET}/{path}', raw, mime)
    try:
        with connect() as db:
            db.execute('insert into visual_memories(id,user_id,name,description,storage_path,mime_type) values (?,?,?,?,?,?)',
                       (item_id, user_id, name, description, path, mime))
    except Exception:
        try:
            _storage('DELETE', f'object/{BUCKET}/{path}')
        except Exception:
            pass
        raise
    return {'id': item_id, 'name': name, 'description': description}


def list_memories(user_id, name=None):
    with connect() as db:
        if name:
            rows = db.execute('select id,name,description,mime_type,created_at from visual_memories where user_id=? and lower(name)=lower(?) order by created_at desc', (user_id, name)).fetchall()
        else:
            rows = db.execute('select id,name,description,mime_type,created_at from visual_memories where user_id=? order by created_at desc limit 100', (user_id,)).fetchall()
    return [{'id': str(r[0]), 'name': r[1], 'description': r[2], 'mime_type': r[3], 'created_at': r[4].isoformat()} for r in rows]


def signed_url(user_id, item_id):
    with connect() as db:
        row = db.execute('select storage_path from visual_memories where user_id=? and id=?', (user_id, item_id)).fetchone()
    if not row:
        raise LookupError('Imagem não encontrada nesta conta.')
    result = _storage('POST', f'object/sign/{BUCKET}/{row[0]}', json.dumps({'expiresIn': 120}).encode())
    signed = result.get('signedURL', '')
    if not signed.startswith('/'):
        raise RuntimeError('Falha ao gerar URL temporária.')
    return _config()[0] + '/storage/v1' + signed


def delete(user_id, item_id):
    with connect() as db:
        row = db.execute('select storage_path from visual_memories where user_id=? and id=?', (user_id, item_id)).fetchone()
        if not row:
            raise LookupError('Imagem não encontrada nesta conta.')
        _storage('DELETE', f'object/{BUCKET}/{row[0]}')
        db.execute('delete from visual_memories where user_id=? and id=?', (user_id, item_id))
