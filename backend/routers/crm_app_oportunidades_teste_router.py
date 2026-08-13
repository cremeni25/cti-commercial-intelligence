from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/crm-app/oportunidades", tags=["CRM App"])


def _admin(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente ADMIN_MASTER pode administrar registros de teste.")
    return usuario


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()
