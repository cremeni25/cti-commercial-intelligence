"""Normalização central de credenciais do backend CTI.

O Render inicia o Python com a pasta ``backend`` no sys.path. O módulo
``sitecustomize`` é carregado automaticamente pelo interpretador e garante
que routers legados que ainda consultam SUPABASE_KEY utilizem a credencial
administrativa nas operações internas do servidor.

A chave pública continua disponível no frontend por suas próprias variáveis;
esta normalização ocorre somente dentro do processo privado do backend.
"""

import os

service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if service_role_key:
    os.environ["SUPABASE_KEY"] = service_role_key
    os.environ["CTI_SUPABASE_CREDENTIAL_ROLE"] = "service_role"
else:
    os.environ.setdefault("CTI_SUPABASE_CREDENTIAL_ROLE", "public_or_anon")
