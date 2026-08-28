from __future__ import annotations

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_core_extension import nucleo_comercial

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro"])

PERFIS_ESCOPO_PROPRIO = {
    "REPRES_REGIAO_01",
    "REPRES_REGIAO_02",
    "INDICADOR_VIENA_SP",
}


def _visao_consolidada(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP"
        and bool(usuario.permissoes.get("acesso_total"))
    )


def _filtrar_por_usuario(registros: list[dict], usuario: UsuarioAutenticado) -> list[dict]:
    if _visao_consolidada(usuario):
        return registros
    if usuario.tipo_usuario not in PERFIS_ESCOPO_PROPRIO:
        # USUARIO_CTI permanece com o comportamento atual até definição
        # específica de governança (caso administrativo da Gessica).
        return registros
    return [
        item
        for item in registros
        if str(item.get("responsavel_id") or "") == str(usuario.id)
    ]


@router.get("/nucleo-comercial")
def nucleo_comercial_seguro(
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Núcleo canônico com enforcement de escopo baseado no login autenticado."""
    return _filtrar_por_usuario(nucleo_comercial(), usuario)
