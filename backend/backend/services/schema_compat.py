"""Ponte de compatibilidade para o layout usado pelo Render.

O serviço inicia com `backend/` como diretório raiz. O código histórico também
é importado em testes a partir da raiz do repositório. Esta ponte mantém ambos
os modos sem duplicar implementação.
"""

from services.schema_compat import (
    insert_schema_compatible,
    missing_column_from_error,
    update_schema_compatible,
)

__all__ = [
    "missing_column_from_error",
    "insert_schema_compatible",
    "update_schema_compatible",
]
