from contextlib import contextmanager
import os, sqlite3, secrets, hashlib, hmac, time
from datetime import date, datetime
from pathlib import Path
from fastapi import HTTPException

DB = Path(__file__).resolve().parents[2] / 'data' / 'auth_users.sqlite3'

def connect():
    if os.getenv('DATABASE_URL'):
        from app.security.postgres import connect as postgres_connect
        return postgres_connect()
    DB.parent.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(DB, timeout=10)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, salt BLOB NOT NULL, digest BLOB NOT NULL)')
    cols={r[1] for r in c.execute('PRAGMA table_info(users)')}
    for column,definition in [('full_name','TEXT'),('birth_date','TEXT'),('age_verified_at','TEXT'),('guardian_email','TEXT'),('guardian_approved_at','TEXT'),('is_admin','INTEGER NOT NULL DEFAULT 0'),('created_at','TEXT'),('last_login_at','TEXT')]:
        if column not in cols: c.execute(f'ALTER TABLE users ADD COLUMN {column} {definition}')
    c.execute("UPDATE users SET created_at = NULL WHERE created_at = ''")
    c.execute('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires INTEGER NOT NULL)')
    c.commit()
    return c


@contextmanager
def managed_connect():
    conn = connect()
    try:
        with conn:
            yield conn
    finally:
        # SQLite: o context manager confirma/reverte, mas nao fecha a conexao.
        # PostgreSQL: Connection.__exit__ ja fecha a conexao interna.
        if isinstance(conn, sqlite3.Connection):
            conn.close()

def digest(password,salt): return hashlib.pbkdf2_hmac('sha256',password.encode(),salt,310000)
def validate_profile(full_name, birth_date):
    name=(full_name or '').strip()
    if not (2 <= len(name) <= 120): raise HTTPException(422,'Informe o nome completo (2 a 120 caracteres).')
    try:
        born=date.fromisoformat(birth_date)
    except (TypeError,ValueError):
        raise HTTPException(422,'Data de nascimento inválida (AAAA-MM-DD).')
    today=date.today()
    if born>today or born.year<1900: raise HTTPException(422,'Data de nascimento inválida.')
    age=today.year-born.year-((today.month,today.day)<(born.month,born.day))
    return name,born.isoformat()

def age_group(birth_date):
    if not birth_date: return 'unknown'
    born=date.fromisoformat(birth_date); today=date.today()
    age=today.year-born.year-((today.month,today.day)<(born.month,born.day))
    return 'child' if age<13 else 'teen' if age<18 else 'adult'

def profile(user_id):
    with managed_connect() as c:
        r=c.execute('SELECT id,email,full_name,birth_date,guardian_email,guardian_approved_at,is_admin FROM users WHERE id=?',(user_id,)).fetchone()
    if not r: raise HTTPException(401,'Usuário não encontrado.')
    group=age_group(r[3]); approved=bool(r[5]); return {'user_id':r[0],'email':r[1],'full_name':r[2], 'birth_date':r[3], 'age_group':group, 'guardian_email':r[4], 'guardian_approved':approved, 'profile_complete':bool(r[2] and r[3]), 'access_ready':bool(r[2] and r[3]) and (group=='adult' or approved), 'is_admin':bool(r[6])}

def update_profile(user_id, full_name, birth_date, guardian_email=None):
    name,born=validate_profile(full_name,birth_date)
    group=age_group(born)
    if os.getenv('ASHLEY_COMMERCIAL_MODE', '0') == '1' and group != 'adult':
        raise HTTPException(403, 'A edição comercial exige idade mínima de 18 anos.')
    guardian=(guardian_email or '').strip().lower() if group!='adult' else None
    if group!='adult' and (not guardian or '@' not in guardian): raise HTTPException(422,'Informe o e-mail do responsável legal.')
    with managed_connect() as c:
        c.execute('UPDATE users SET full_name=?, birth_date=?, age_verified_at=?, guardian_email=?, guardian_approved_at=NULL WHERE id=?',(name,born,datetime.now().isoformat(),guardian,user_id))
    return profile(user_id)

def create(email,password,full_name=None,birth_date=None,guardian_email=None):
    email=email.strip().lower()
    if not (3 <= len(email) <= 254 and '@' in email and 12 <= len(password) <= 256): raise HTTPException(422,'E-mail válido e senha de pelo menos 12 caracteres são necessários.')
    name,born=validate_profile(full_name,birth_date)
    if age_group(born)!='adult': raise HTTPException(403,'A primeira conta administrativa deve ser de um adulto. Use o cadastro de usuário para menores.')
    with managed_connect() as c:
        if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]: raise HTTPException(403,'Conta administrativa inicial já criada.')
        salt=secrets.token_bytes(16)
        c.execute('INSERT INTO users(email,salt,digest,full_name,birth_date,age_verified_at,is_admin,created_at) VALUES(?,?,?,?,?,?,TRUE,?)',(email,salt,digest(password,salt),name,born,datetime.now().isoformat(),datetime.now().astimezone().isoformat()))
        c.commit()
        return c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()[0]

def login(email,password):
    with managed_connect() as c:
        r=c.execute('SELECT id,salt,digest FROM users WHERE email=?',(email.strip().lower(),)).fetchone()
        if not r or not hmac.compare_digest(digest(password,r[1]),r[2]): raise HTTPException(401,'Credenciais inválidas.')
        token=secrets.token_urlsafe(40); exp=int(time.time())+86400
        c.execute('UPDATE users SET last_login_at=? WHERE id=?',(datetime.now().astimezone().isoformat(),r[0]))
        c.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),r[0],exp))
        c.commit()
        return {'access_token':token,'token_type':'bearer','user_id':r[0],'expires_at':exp}

def identity(token):
    if not token: raise HTTPException(401,'Login necessário.')
    with managed_connect() as c:
        r=c.execute('SELECT user_id FROM sessions WHERE token_hash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
        if not r: raise HTTPException(401,'Sessão inválida ou expirada.')
        return r[0]

def logout(token):
    with managed_connect() as c: c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))


def register_user(email,password,full_name,birth_date,guardian_email=None):
    email=email.strip().lower(); name,born=validate_profile(full_name,birth_date)
    if not (3<=len(email)<=254 and '@' in email and 12<=len(password)<=256): raise HTTPException(422,'E-mail válido e senha de pelo menos 12 caracteres são necessários.')
    group=age_group(born); guardian=(guardian_email or '').strip().lower()
    if os.getenv('ASHLEY_COMMERCIAL_MODE', '0') == '1' and group != 'adult':
        raise HTTPException(403, 'Cadastros de menores indisponíveis na edição comercial.')
    if group!='adult' and (not guardian or '@' not in guardian or guardian==email): raise HTTPException(422,'Informe e-mail válido e diferente para o responsável legal.')
    with managed_connect() as c:
        if not c.execute('SELECT COUNT(*) FROM users').fetchone()[0]: raise HTTPException(403,'Crie primeiro a conta administrativa.')
        salt=secrets.token_bytes(16)
        try:
            sql='INSERT INTO users(email,salt,digest,full_name,birth_date,age_verified_at,guardian_email,created_at) VALUES(?,?,?,?,?,?,?,?)'
            if os.getenv('DATABASE_URL'):
                cur=c.execute(sql+' RETURNING id',(email,salt,digest(password,salt),name,born,datetime.now().isoformat(),guardian if group!='adult' else None,datetime.now().astimezone().isoformat()))
                user_id=cur.fetchone()[0]
            else:
                cur=c.execute(sql,(email,salt,digest(password,salt),name,born,datetime.now().isoformat(),guardian if group!='adult' else None,datetime.now().astimezone().isoformat()))
                user_id=cur.lastrowid
            return {'created':True,'user_id':user_id,'age_group':group,'guardian_approval_required':group!='adult'}
        except Exception as exc:
            if isinstance(exc, sqlite3.IntegrityError):
                raise HTTPException(409, 'E-mail já cadastrado.') from exc
            try:
                from psycopg.errors import UniqueViolation
            except ImportError:
                UniqueViolation = ()
            if UniqueViolation and isinstance(exc, UniqueViolation):
                raise HTTPException(409, 'E-mail já cadastrado.') from exc
            raise

def guardian_children(guardian_user_id):
    guardian=profile(guardian_user_id)
    if guardian['age_group']!='adult': raise HTTPException(403,'Responsável precisa ser adulto.')
    with managed_connect() as c:
        rows=c.execute('SELECT id,full_name,birth_date,guardian_approved_at FROM users WHERE guardian_email=?',(guardian['email'],)).fetchall()
    return [{'user_id':r[0],'full_name':r[1],'age_group':age_group(r[2]),'approved':bool(r[3])} for r in rows]

def guardian_approve(guardian_user_id,child_id,approved):
    # Sem confirmação independente do vínculo parental, esta autorização não é segura para produção.
    if os.getenv('ASHLEY_ENV', 'development').lower() == 'production':
        raise HTTPException(503, 'Autorização de responsáveis indisponível até integrar verificação de identidade e vínculo parental.')
    guardian=profile(guardian_user_id)
    if guardian['age_group']!='adult': raise HTTPException(403,'Somente adultos podem autorizar.')
    with managed_connect() as c:
        row=c.execute('SELECT birth_date FROM users WHERE id=? AND guardian_email=?',(child_id,guardian['email'])).fetchone()
        if not row or age_group(row[0])=='adult': raise HTTPException(404,'Conta de menor não vinculada a este responsável.')
        c.execute('UPDATE users SET guardian_approved_at=? WHERE id=?',(datetime.now().isoformat() if approved else None,child_id))
    return {'ok':True,'approved':approved}


def require_admin(token):
    """Exige sessao valida e permissao administrativa explicita."""
    user_id = identity(token)
    usuario = profile(user_id)

    if not usuario.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito ao administrador."
        )

    if usuario.get("age_group") != "adult":
        raise HTTPException(
            status_code=403,
            detail="Administracao restrita a adultos."
        )

    return user_id
