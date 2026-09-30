from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_router import _pedido_autorizado, _usa_escopo_proprio, _visao_consolidada
from routers.crm_router import obter_oportunidade
from routers.vendas_router import listar_vendas

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-vendas"])


def _responsavel_venda(venda: dict) -> str:
    direto = str(venda.get("responsavel_id") or venda.get("usuario_id") or venda.get("vendedor_id") or "").strip()
    if direto:
        return direto
    oportunidade_id = str(venda.get("oportunidade_id") or "").strip()
    if oportunidade_id:
        try:
            oportunidade = obter_oportunidade(oportunidade_id)
        except HTTPException:
            oportunidade = {}
        return str(oportunidade.get("responsavel_id") or oportunidade.get("usuario_id") or "").strip()
    return ""


def _venda_autorizada(venda: dict, usuario: UsuarioAutenticado) -> bool:
    if _visao_consolidada(usuario) or not _usa_escopo_proprio(usuario):
        return True
    if _responsavel_venda(venda) == str(usuario.id):
        return True
    pedido_id = str(venda.get("pedido_id") or "").strip()
    if pedido_id:
        try:
            _pedido_autorizado(pedido_id, usuario)
            return True
        except HTTPException:
            return False
    return False


@router.get("/vendas")
def listar_vendas_seguras(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    resultado = []
    for venda in listar_vendas():
        if not _venda_autorizada(venda, usuario):
            continue
        item = dict(venda)
        responsavel_id = _responsavel_venda(item)
        if not responsavel_id and _usa_escopo_proprio(usuario) and not _visao_consolidada(usuario):
            responsavel_id = str(usuario.id)
        item["responsavel_id"] = responsavel_id or None
        resultado.append(item)
    return resultado
