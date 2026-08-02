"""Inicialização central dos routers internos do CTI.

Todo router importado pelo backend é carregado após este módulo. Em produção,
as operações internas devem usar a service role para não serem bloqueadas por
RLS. A chave pública permanece disponível apenas no frontend.
"""

import os

_service_role = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if _service_role:
    os.environ["SUPABASE_KEY"] = _service_role

# A extensão importa e amplia o router CRM antes de ele ser incluído no FastAPI.
# Assim, todos os módulos passam a poder consumir a mesma projeção comercial.
from . import crm_core_extension as _crm_core_extension  # noqa: E402,F401
