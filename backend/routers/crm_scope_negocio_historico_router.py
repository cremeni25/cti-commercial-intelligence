from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_router import obter_oportunidade
from routers.negociacoes_router import timeline_oportunidade

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-negocio-historico"])

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


def _usa_escopo_proprio(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario in PERFIS_ESCOPO_PROPRIO


def _oportunidade_autorizada(oportunidade_id: str, usuario: UsuarioAutenticado) -> dict:
    oportunidade = obter_oportunidade(oportunidade_id)
    if _visao_consolidada(usuario) or not _usa_escopo_proprio(usuario):
        return oportunidade
    if str(oportunidade.get("responsavel_id") or "") == str(usuario.id):
        return oportunidade
    raise HTTPException(status_code=404, detail="Oportunidade comercial não encontrada")


@router.get("/timeline/{oportunidade_id}")
def timeline_oportunidade_segura(
    oportunidade_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _oportunidade_autorizada(oportunidade_id, usuario)
    return timeline_oportunidade(oportunidade_id)
