from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.clientes_oportunidade_router import ClienteCreate, criar_cliente_crm_app
from routers.crm_app_clientes_edicao_router import ClienteEdicao, atualizar_cliente_crm_app, obter_cliente_crm_app

router = APIRouter(prefix="/crm-seguro/clientes", tags=["crm-seguro-clientes"])


def _visao_total(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP"
        and bool(usuario.permissoes.get("acesso_total"))
    )


def _exigir_permissao(usuario: UsuarioAutenticado, permissao: str) -> None:
    if _visao_total(usuario) or bool(usuario.permissoes.get(permissao)):
        return
    raise HTTPException(status_code=403, detail="Usuário sem permissão para esta operação cadastral.")


@router.post("")
def criar_cliente_seguro(
    dados: ClienteCreate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_permissao(usuario, "clientes_editar")
    return criar_cliente_crm_app(dados)


@router.get("/{cliente_id}")
def obter_cliente_seguro(
    cliente_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_permissao(usuario, "clientes_visualizar")
    return obter_cliente_crm_app(cliente_id)


@router.put("/{cliente_id}")
def atualizar_cliente_seguro(
    cliente_id: str,
    dados: ClienteEdicao,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_permissao(usuario, "clientes_editar")
    return atualizar_cliente_crm_app(cliente_id, dados)
