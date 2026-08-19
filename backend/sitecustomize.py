"""Bootstrap privado do backend CTI.

Executado automaticamente pelo Python antes da aplicação. Normaliza a
credencial administrativa e limita pools nativos de bibliotecas numéricas,
reduzindo memória residente na instância Render de 512 MB.
"""

import os

for _variavel in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_variavel, "1")

service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if service_role_key:
    os.environ["SUPABASE_KEY"] = service_role_key
    os.environ["CTI_SUPABASE_CREDENTIAL_ROLE"] = "service_role"
else:
    os.environ.setdefault("CTI_SUPABASE_CREDENTIAL_ROLE", "public_or_anon")

os.environ.setdefault("CTI_MEMORY_POLICY", "render_512mb")
