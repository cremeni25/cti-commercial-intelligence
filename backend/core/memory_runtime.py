from __future__ import annotations

import os

# Instância Render atual: 512 MB. Bibliotecas numéricas podem abrir pools de
# threads e reservar memória desnecessária para a carga predominantemente I/O
# do CTI. Os defaults abaixo são aplicados antes de numpy/pandas serem carregados.
for _variavel in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_variavel, "1")


def runtime_memory_policy() -> dict[str, str]:
    return {
        "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS", "1"),
        "omp_threads": os.environ.get("OMP_NUM_THREADS", "1"),
        "mkl_threads": os.environ.get("MKL_NUM_THREADS", "1"),
        "numexpr_threads": os.environ.get("NUMEXPR_NUM_THREADS", "1"),
        "policy": "cti_render_512mb",
    }
