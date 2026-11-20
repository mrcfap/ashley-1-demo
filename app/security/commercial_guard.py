"""Verificações defensivas de escopo de identidade para edição comercial."""
import re
from email.parser import BytesParser
from email.policy import default

# Somente segmentos que efetivamente representam user_id (não case_id etc.).
_USER_PATHS = (
    re.compile(r"^/diagnostico/usuario/(\d+)$"),
    re.compile(r"^/memoria/buscar/(\d+)$"),
    re.compile(r"^/casos/(\d+)(?:/\d+)?$"),
    re.compile(r"^/evolucao/(\d+)$"),
    re.compile(r"^/evolucao-v11/(\d+)$"),
    re.compile(r"^/vision/session/(\d+)$"),
    re.compile(r"^/vision/cognitive-hub/(\d+)$"),
    re.compile(r"^/vision/presence/status/(\d+)$"),
    re.compile(r"^/vision/presence/stop/(\d+)$"),
)

def forbidden_identity_in_url(path, query, authenticated_user_id):
    uid = int(authenticated_user_id)
    for pattern in _USER_PATHS:
        match = pattern.fullmatch(path)
        if match and int(match.group(1)) != uid:
            return True
    # Se há múltiplos parâmetros user_id, todos precisam coincidir.
    values = query.getlist('user_id') if hasattr(query, 'getlist') else ([query['user_id']] if 'user_id' in query else [])
    for value in values:
        try:
            if int(value) != uid:
                return True
        except (TypeError, ValueError):
            return True
    return False

def multipart_user_id(body, content_type):
    """Lê somente campos user_id de um multipart já recebido; falha fechado."""
    try:
        raw = (b'MIME-Version: 1.0\r\nContent-Type: ' + content_type.encode('ascii') + b'\r\n\r\n' + body)
        msg = BytesParser(policy=default).parsebytes(raw)
        if not msg.is_multipart():
            return None
        values = []
        for part in msg.iter_parts():
            if part.get_param('name', header='content-disposition') == 'user_id':
                values.append(int(part.get_content().strip()))
        return values[0] if len(values) == 1 else None
    except (ValueError, TypeError, UnicodeError, LookupError):
        return None
