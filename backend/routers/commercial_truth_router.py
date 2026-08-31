from fastapi import APIRouter, Depends, Query

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_estrategia_router import _consolidado
from services.commercial_truth import consolidar_verdade_comercial

router = APIRouter()


@router.get('/analytics/verdade-comercial')
def verdade_comercial(
    limite_clientes: int = Query(default=200, ge=1, le=500),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Correlaciona evidências ANFIR, Funil e CRM sem fundir ou reescrever fontes."""
    return consolidar_verdade_comercial(
        usuario_id=str(usuario.id),
        master=bool(_consolidado(usuario)),
        limite_clientes=limite_clientes,
    )
