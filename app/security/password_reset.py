"""Password recovery. SMTP credentials must be configured in environment."""
import hashlib,os,secrets,smtplib,time
from email.message import EmailMessage
from fastapi import HTTPException
from app.security import auth

def _table(c):
    c.execute('CREATE TABLE IF NOT EXISTS password_resets (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires BIGINT NOT NULL, used INTEGER NOT NULL DEFAULT 0)')

def request_reset(email):
    generic={'ok':True,'message':'Se a conta existir, você receberá instruções no e-mail cadastrado.'}
    if not all(os.getenv(x) for x in ('SMTP_HOST','SMTP_USER','SMTP_PASSWORD','ASHLEY_PUBLIC_URL','SMTP_FROM')):
        raise HTTPException(503,'Recuperação por e-mail ainda não configurada. Configure SMTP no servidor.')
    with auth.managed_connect() as c:
        _table(c)
        row=c.execute('SELECT id FROM users WHERE email=?',(email.strip().lower(),)).fetchone()
        if not row:return generic
        user_id=row[0]
        # Avoid repeated reset requests within 60 seconds.
        recent=c.execute('SELECT expires FROM password_resets WHERE user_id=? AND used=0 ORDER BY expires DESC LIMIT 1',(user_id,)).fetchone()
        if recent and recent[0]>int(time.time())+840:return generic
        token=secrets.token_urlsafe(32); token_hash=hashlib.sha256(token.encode()).hexdigest()
        c.execute('INSERT INTO password_resets (token_hash,user_id,expires,used) VALUES (?,?,?,0)',(token_hash,user_id,int(time.time())+900))
    msg=EmailMessage();msg['Subject']='Ashley 1.0 — Recuperação de senha';msg['From']=os.environ['SMTP_FROM'];msg['To']=email.strip().lower()
    link=os.environ['ASHLEY_PUBLIC_URL'].rstrip('/')+'/?reset_token='+token
    msg.set_content('Para redefinir sua senha, acesse o link (válido por 15 minutos):\n'+link+'\nSe não solicitou, ignore.')
    try:
        with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','587')),timeout=12) as server:
            server.starttls();server.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD']);server.send_message(msg)
    except Exception:
        # Don't disclose token; invalidate unsent reset.
        with auth.managed_connect() as c:c.execute('UPDATE password_resets SET used=1 WHERE token_hash=?',(token_hash,))
        raise HTTPException(503,'Serviço de e-mail temporariamente indisponível.')
    return generic

def confirm_reset(token,password):
    if len(password)<12 or len(password)>256:raise HTTPException(422,'A senha deve ter entre 12 e 256 caracteres.')
    token_hash=hashlib.sha256(token.encode()).hexdigest()
    with auth.managed_connect() as c:
        _table(c)
        row=c.execute('SELECT user_id FROM password_resets WHERE token_hash=? AND used=0 AND expires>?',(token_hash,int(time.time()))).fetchone()
        if not row:raise HTTPException(400,'Link inválido ou expirado.')
        salt=secrets.token_bytes(16)
        c.execute('UPDATE users SET salt=?,digest=? WHERE id=?',(salt,auth.digest(password,salt),row[0]))
        c.execute('UPDATE password_resets SET used=1 WHERE user_id=?',(row[0],))
        c.execute('DELETE FROM sessions WHERE user_id=?',(row[0],))
    return {'ok':True,'message':'Senha atualizada. Entre novamente.'}
