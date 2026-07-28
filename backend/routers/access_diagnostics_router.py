from __future__ import annotations

import base64
import json
import os
from urllib.parse import urlparse

from fastapi import APIRouter

from core.supabase_client import supabase

router = APIRouter(prefix="/auth/access-requests", tags=["auth-diagnostics"])


def _project_ref() -> str:
    host = urlparse(os.getenv("SUPABASE_URL", "")).hostname or ""
    return host.split(".", 1)[0] if host else "desconhecido"


def _configured_role() -> str:
    token = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        return str(decoded.get("role") or "desconhecido")
    except Exception:
        return "não-identificado"


@router.get("/health")
def access_requests_health():
    try:
        resposta = supabase.table("cti_access_requests").select("id").limit(1).execute()
        return {
            "status": "ready",
            "project_ref": _project_ref(),
            "credential_role": _configured_role(),
            "table": "cti_access_requests",
            "readable": True,
            "rows_sampled": len(getattr(resposta, "data", None) or []),
        }
    except Exception as exc:
        return {
            "status": "blocked",
            "project_ref": _project_ref(),
            "credential_role": _configured_role(),
            "table": "cti_access_requests",
            "readable": False,
            "error_type": type(exc).__name__,
            "error": str(exc)[:300],
        }
