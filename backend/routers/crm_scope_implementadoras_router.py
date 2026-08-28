from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_estrategia_router import _anfir_do_usuario, _metadata_escopo
from services.base_analytics import consolidar_implementadoras

router = APIRouter(prefix="/crm-seguro/implementadoras", tags=["crm-seguro-implementadoras"])


@router.get("")
def listar_implementadoras_seguras(
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    registros, inicio_efetivo, fim_efetivo = _anfir_do_usuario(
        usuario, contexto, periodo, uf, ddd, inicio, fim
    )
    return {
        "itens": consolidar_implementadoras(registros),
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "uf": uf,
            "ddd": ddd,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
            "escopo_usuario": _metadata_escopo(usuario),
        },
    }
