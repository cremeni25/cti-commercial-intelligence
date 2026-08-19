"""Bootstrap privado do backend CTI.

Executado automaticamente pelo Python antes da aplicação. Normaliza a
credencial administrativa, limita pools nativos e mantém pandas em import
lazy para preservar margem na instância Render de 512 MB.
"""

import importlib.util
import os
import sys


# Bibliotecas numéricas podem reservar pools nativos acima da necessidade do
# CTI. A carga é predominantemente I/O; um thread por pool é suficiente.
for _variavel in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_variavel, "1")


def _instalar_import_lazy(nome_modulo: str) -> None:
    """Adia execução de módulo pesado até o primeiro uso real de atributo."""
    if nome_modulo in sys.modules:
        return
    try:
        spec = importlib.util.find_spec(nome_modulo)
        if spec is None or spec.loader is None:
            return
        loader = importlib.util.LazyLoader(spec.loader)
        spec.loader = loader
        modulo = importlib.util.module_from_spec(spec)
        sys.modules[nome_modulo] = modulo
        loader.exec_module(modulo)
    except Exception:
        # Falha no modo lazy nunca pode impedir o backend de iniciar; o import
        # convencional ocorrerá normalmente quando o módulo for solicitado.
        sys.modules.pop(nome_modulo, None)


# main.py legado ainda possui `import pandas as pd`. Com LazyLoader isso não
# executa pandas/numpy no bootstrap; somente endpoints que realmente usam
# planilhas/analytics pagam esse custo.
_instalar_import_lazy("pandas")

service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if service_role_key:
    os.environ["SUPABASE_KEY"] = service_role_key
    os.environ["CTI_SUPABASE_CREDENTIAL_ROLE"] = "service_role"
else:
    os.environ.setdefault("CTI_SUPABASE_CREDENTIAL_ROLE", "public_or_anon")

os.environ.setdefault("CTI_MEMORY_POLICY", "render_512mb_lazy_pandas")
