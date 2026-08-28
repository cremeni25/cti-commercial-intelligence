from __future__ import annotations

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.clientes_oportunidade_router import ClienteCreate, criar_cliente_crm_app
from routers.crm_app_clientes_edicao_router import ClienteEdicao, atualizar_cliente_crm_app, obter_cliente_crm_app

router = APIRouter(prefix="/crm-seguro/clientes", tags=["crm-seguro-clientes"])


@router.post("")
def criar_cliente_seguro(
    dados: ClienteCreate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return criar_cliente_crm_app(dados)


@router.get("/{cliente_id}")
def obter_cliente_seguro(
    cliente_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return obter_cliente_crm_app(cliente_id)


@router.put("/{cliente_id}")
def atualizar_cliente_seguro(
    cliente_id: str,
    dados: ClienteEdicao,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return atualizar_cliente_crm_app(cliente_id, dados)
