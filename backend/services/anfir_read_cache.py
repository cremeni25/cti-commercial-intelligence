from __future__ import annotations

import os
from threading import RLock, Thread
from time import monotonic
from typing import Any

from repositories.cti_repository import repository

# ANFIR é uma fonte histórica/consolidada. O cache é somente de leitura e fica
# dentro do processo do backend; não altera persistência, RBAC ou filtros.
_CACHE_TTL_SECONDS = float(os.getenv("CTI_ANFIR_READ_CACHE_SECONDS", "300") or 300)
_lock = RLock()
_cache: dict[str, Any] = {
    "expires_at": 0.0,
    "source_id": None,
    "registros": None,
}


def _source_id() -> int:
    fonte = repository.buscar_cti_anfir
    funcao = getattr(fonte, "__func__", fonte)
    return id(funcao)


def fonte_anfir() -> list[dict[str, Any]]:
    agora = monotonic()
    origem = _source_id()
    registros = _cache.get("registros")
    if (
        registros is not None
        and _cache.get("source_id") == origem
        and agora < float(_cache.get("expires_at") or 0)
    ):
        return registros

    # Evita que as três leituras do Dashboard façam a mesma paginação pesada
    # simultaneamente quando o cache expira.
    with _lock:
        agora = monotonic()
        origem = _source_id()
        registros = _cache.get("registros")
        if (
            registros is not None
            and _cache.get("source_id") == origem
            and agora < float(_cache.get("expires_at") or 0)
        ):
            return registros

        carregados = list(repository.buscar_cti_anfir() or [])
        _cache["registros"] = carregados
        _cache["source_id"] = origem
        _cache["expires_at"] = monotonic() + max(_CACHE_TTL_SECONDS, 1.0)
        return carregados


def invalidar_cache_anfir() -> None:
    with _lock:
        _cache["expires_at"] = 0.0
        _cache["source_id"] = None
        _cache["registros"] = None


def preaquecer_anfir_async() -> None:
    if os.getenv("CTI_PREWARM_ANFIR", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return

    def carregar() -> None:
        try:
            fonte_anfir()
        except Exception as exc:
            # Preaquecimento não pode impedir o backend de subir. A próxima
            # leitura tentará carregar novamente pelo fluxo normal.
            print("CTI_ANFIR_PREWARM_FALHOU", str(exc))

    Thread(target=carregar, name="cti-anfir-prewarm", daemon=True).start()
