import os
import threading

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


class _ThreadLocalSupabase:
    """Entrega um Client Supabase independente para cada worker thread.

    O FastAPI executa endpoints síncronos em um threadpool. Compartilhar uma única
    instância global do httpx/http2 entre essas threads pode corromper o estado
    interno do HPACK e provocar falhas como ``deque mutated during iteration`` e
    ``Resource temporarily unavailable``. O proxy preserva a API já usada pelo
    restante do backend, mas elimina o compartilhamento concorrente da sessão.
    """

    def __init__(self, url: str, key: str) -> None:
        self._url = url
        self._key = key
        self._local = threading.local()

    def _client(self) -> Client:
        client = getattr(self._local, "client", None)
        if client is None:
            client = create_client(self._url, self._key)
            self._local.client = client
        return client

    def __getattr__(self, name: str):
        return getattr(self._client(), name)


supabase = _ThreadLocalSupabase(SUPABASE_URL, SUPABASE_BACKEND_KEY)
