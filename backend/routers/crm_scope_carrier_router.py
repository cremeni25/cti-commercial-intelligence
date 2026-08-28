from __future__ import annotations

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.carrier_operacional_router import detalhe_pedido
from routers.crm_scope_router import _pedido_autorizado

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro"])


@router.get("/pedidos/{pedido_id}/carrier-pacote")
def detalhe_pedido_carrier_seguro(
    pedido_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _pedido_autorizado(pedido_id, usuario)
    return detalhe_pedido(pedido_id)
