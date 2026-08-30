from datetime import date

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_estrategia_router import _anfir_do_usuario, _metadata_escopo
from services.anfir_workbook_contract import consolidar_workbook_anfir_2026


router = APIRouter()


@router.get("/analytics/anfir-workbook-2026")
def anfif_workbook_2026(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """Contrato funcional e seguro da auditoria ANFIR Carrier/JOV 2026.

    A fotografia permanece fixa em Viena SP + competência 2026, mas a base
    entregue ao consolidado respeita o mesmo escopo RBAC territorial já
    homologado nas rotas estratégicas seguras. Não grava nem altera registros.
    """
    registros, _, _ = _anfir_do_usuario(
        usuario,
        contexto="viena-sp",
        periodo="PERSONALIZADO",
        uf=None,
        ddd=None,
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )
    payload = consolidar_workbook_anfir_2026(registros)
    payload.setdefault("metadata", {})["escopo_usuario"] = _metadata_escopo(usuario)
    return payload
