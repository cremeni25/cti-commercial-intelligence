import os

from supabase import Client, create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# O backend executa operações administrativas (Auth Admin e tabelas protegidas por RLS).
# Em produção, a chave service_role deve ser configurada separadamente no Render.
# O fallback mantém compatibilidade com ambientes já existentes e com os testes de CI.
SUPABASE_BACKEND_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_BACKEND_KEY:
    raise RuntimeError(
        "Configuração Supabase incompleta: defina SUPABASE_URL e "
        "SUPABASE_SERVICE_ROLE_KEY (ou SUPABASE_KEY para compatibilidade)."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_BACKEND_KEY)
