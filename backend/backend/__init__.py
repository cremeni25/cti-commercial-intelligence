"""Compatibilidade para execução do backend com ``backend/`` como diretório raiz.

O Render inicia a aplicação dentro da pasta ``backend``. Alguns routers legados ainda
leem ``SUPABASE_KEY`` diretamente ao criar um cliente próprio. Antes que esses módulos
sejam importados, promovemos a chave administrativa já configurada no serviço para que
as operações internas do CRM não sejam bloqueadas pelas políticas RLS.
"""

import os

_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
if _service_role_key:
    os.environ["SUPABASE_KEY"] = _service_role_key
