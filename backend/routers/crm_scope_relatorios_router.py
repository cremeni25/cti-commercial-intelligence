from __future__ import annotations

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_router import _filtrar_por_usuario
from routers.crm_scope_vendas_router import listar_vendas_seguras
from routers.crm_router import listar_oportunidades
from routers.documentos_comerciais_listagem_router import listar_pedidos_operacionais, listar_propostas_operacionais

router = APIRouter(prefix="/crm-seguro/relatorios", tags=["crm-seguro-relatorios"])

_STATUS_TERMINAIS = {"GANHO", "GANHA", "PERDIDO", "PERDIDA", "ENCERRADO", "ENCERRADA", "CONCLUIDO", "CONCLUIDA", "CONCLUÍDO", "CONCLUÍDA", "VENDIDO", "VENDIDA"}


def _status_normalizado(item: dict) -> str:
    return str(item.get("status") or item.get("status_oportunidade") or item.get("situacao") or "").strip().upper()


def _oportunidade_ativa(item: dict) -> bool:
    """Carteira operacional contém somente negócios ainda em andamento.

    Estados terminais permanecem preservados na base e no histórico realizado,
    mas não podem compor Oportunidades/Pipeline/Forecast ativos.
    """
    return _status_normalizado(item) not in _STATUS_TERMINAIS


@router.get("")
def relatorio_comercial_seguro(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """Relatório comercial separado por etapa real da jornada."""
    oportunidades_usuario = _filtrar_por_usuario(listar_oportunidades(), usuario)
    oportunidades_ativas = [item for item in oportunidades_usuario if _oportunidade_ativa(item)]
    return {
        "oportunidades": oportunidades_ativas,
        "propostas": _filtrar_por_usuario(listar_propostas_operacionais(), usuario),
        "pedidos": _filtrar_por_usuario(listar_pedidos_operacionais(), usuario),
        "vendas": listar_vendas_seguras(usuario),
    }
