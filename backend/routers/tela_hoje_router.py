"""Tela "Hoje" (qualquer usuário autenticado; cada um vê o próprio escopo)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_router import _visao_consolidada
from services import tela_hoje

router = APIRouter(prefix="/crm-seguro", tags=["Hoje"])


@router.get("/hoje")
def hoje(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    p = usuario.permissoes or {}
    consolidado = _visao_consolidada(usuario)
    pode_comercial = consolidado or bool(p.get("oportunidades_visualizar") or p.get("oportunidades_editar") or p.get("clientes_visualizar"))
    master = str(usuario.tipo_usuario or "").upper() == "ADMIN_MASTER"
    return tela_hoje.montar(str(usuario.id), consolidado, master, pode_comercial)
