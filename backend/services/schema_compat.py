import re
from typing import Any


_MISSING_COLUMN_PATTERNS = (
    re.compile(r"Could not find the '([^']+)' column", re.IGNORECASE),
    re.compile(r"column [\"']?([^\"'\s]+)[\"']?.*does not exist", re.IGNORECASE),
)


def missing_column_from_error(error: Exception) -> str | None:
    message = str(error)
    for pattern in _MISSING_COLUMN_PATTERNS:
        match = pattern.search(message)
        if match:
            return match.group(1)
    return None


def insert_schema_compatible(
    supabase: Any,
    table: str,
    payload: dict[str, Any],
    *,
    protected_fields: set[str] | None = None,
    max_retries: int = 30,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    protected = protected_fields or set()
    current = {key: value for key, value in payload.items() if value is not None}
    removed: dict[str, Any] = {}

    for _ in range(max_retries):
        try:
            result = supabase.table(table).insert(current).execute()
            return result.data or [], {
                "removed_fields": removed,
                "persisted_fields": list(current.keys()),
            }
        except Exception as error:
            missing = missing_column_from_error(error)
            if not missing or missing not in current:
                raise
            if missing in protected:
                raise RuntimeError(
                    f"A coluna obrigatória '{missing}' não existe em {table}."
                ) from error
            removed[missing] = current.pop(missing)

    raise RuntimeError(f"Não foi possível compatibilizar o payload com a tabela {table}.")


def update_schema_compatible(
    supabase: Any,
    table: str,
    record_id: str,
    payload: dict[str, Any],
    *,
    max_retries: int = 30,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    current = {key: value for key, value in payload.items() if value is not None}
    removed: dict[str, Any] = {}

    for _ in range(max_retries):
        try:
            result = supabase.table(table).update(current).eq("id", record_id).execute()
            return result.data or [], {
                "removed_fields": removed,
                "persisted_fields": list(current.keys()),
            }
        except Exception as error:
            missing = missing_column_from_error(error)
            if not missing or missing not in current:
                raise
            removed[missing] = current.pop(missing)

    raise RuntimeError(f"Não foi possível compatibilizar a atualização com a tabela {table}.")
