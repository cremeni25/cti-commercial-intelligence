from fastapi import APIRouter, Depends, HTTPException, Query

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_estrategia_router import _consolidado
from services.commercial_truth import consolidar_verdade_comercial

router = APIRouter()


@router.get('/analytics/verdade-comercial')
def verdade_comercial(
    responsavel_id: str | None = Query(default=None),
    limite_clientes: int = Query(default=200, ge=1, le=500),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Correlaciona evidências ANFIR, Funil e CRM sem fundir ou reescrever fontes."""
    master = bool(_consolidado(usuario))
    if responsavel_id and not master:
        raise HTTPException(status_code=403, detail='Filtro por responsável disponível somente para usuários Master.')
    return consolidar_verdade_comercial(
        usuario_id=str(usuario.id),
        master=master,
        responsavel_id=responsavel_id,
        limite_clientes=limite_clientes,
    )
