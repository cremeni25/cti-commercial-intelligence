from __future__ import annotations

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_router import _filtrar_por_usuario
from routers.crm_scope_vendas_router import listar_vendas_seguras
from routers.crm_router import listar_oportunidades
from routers.documentos_comerciais_listagem_router import listar_pedidos_operacionais, listar_propostas_operacionais

router = APIRouter(prefix="/crm-seguro/relatorios", tags=["crm-seguro-relatorios"])


@router.get("")
def relatorio_comercial_seguro(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """Mantém o relatório operacional, alterando apenas o universo de responsabilidade."""
    return {
        "oportunidades": _filtrar_por_usuario(listar_oportunidades(), usuario),
        "propostas": _filtrar_por_usuario(listar_propostas_operacionais(), usuario),
        "pedidos": _filtrar_por_usuario(listar_pedidos_operacionais(), usuario),
        "vendas": listar_vendas_seguras(usuario),
    }
