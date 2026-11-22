-- Registros antigos permanecem com created_at NULL: não inferir datas.
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;
ALTER TABLE public.users ALTER COLUMN created_at SET DEFAULT NOW();
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);
