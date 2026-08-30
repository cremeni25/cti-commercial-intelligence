from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.crm_scope_estrategia_router import _anfir_do_usuario, _consolidado, _metadata_escopo
from services.anfir_workbook_contract import consolidar_workbook_anfir_2026
from services.commercial_client_scope import filtrar_por_responsabilidade_cliente


router = APIRouter()


def _usuario_alvo(responsavel_id: str, solicitante: UsuarioAutenticado) -> UsuarioAutenticado:
    if not _consolidado(solicitante):
        raise HTTPException(status_code=403, detail="Filtro por responsável disponível somente para usuários Master.")
    dados = (
        supabase.table("cti_users")
        .select("id,auth_id,email,nome,tipo_usuario,ativo")
        .eq("id", responsavel_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not dados or dados[0].get("ativo") is False:
        raise HTTPException(status_code=422, detail="Responsável comercial inválido ou inativo.")
    item = dados[0]
    return UsuarioAutenticado(
        id=str(item.get("id") or responsavel_id),
        auth_id=str(item.get("auth_id") or item.get("id") or responsavel_id),
        email=str(item.get("email") or ""),
        nome=str(item.get("nome") or "Responsável"),
        tipo_usuario=str(item.get("tipo_usuario") or "USUARIO_CTI"),
        permissoes={},
    )


@router.get("/analytics/anfir-workbook-2026")
def anfif_workbook_2026(
    responsavel_id: str | None = Query(default=None),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Contrato funcional e seguro da auditoria ANFIR Carrier/JOV 2026."""
    usuario_efetivo = _usuario_alvo(responsavel_id, usuario) if responsavel_id else usuario
    registros, _, _ = _anfir_do_usuario(
        usuario_efetivo,
        contexto="viena-sp",
        periodo="PERSONALIZADO",
        uf=None,
        ddd=None,
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )
    if not _consolidado(usuario_efetivo):
        registros = filtrar_por_responsabilidade_cliente(list(registros), str(usuario_efetivo.id))
    payload = consolidar_workbook_anfir_2026(registros)
    metadata = payload.setdefault("metadata", {})
    metadata["escopo_usuario"] = _metadata_escopo(usuario) if not responsavel_id else _metadata_escopo(usuario_efetivo)
    metadata["filtro_responsavel_id"] = responsavel_id
    metadata["filtro_aplicado_por_master"] = bool(responsavel_id)
    return payload
