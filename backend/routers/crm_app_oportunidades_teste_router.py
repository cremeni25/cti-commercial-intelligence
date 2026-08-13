from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/crm-app/oportunidades", tags=["CRM App"])


def _admin(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente ADMIN_MASTER pode administrar registros de teste.")
    return usuario


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _auditar(oportunidade: dict, *, acao: str, usuario_id: str, status_anterior: str, status_resultante: str, motivo: str):
    supabase.table("cti_oportunidades_arquivo_auditoria").insert({
        "oportunidade_id": oportunidade.get("id"),
        "acao": acao,
        "usuario_id": usuario_id,
        "motivo": motivo,
        "status_anterior": status_anterior,
        "status_resultante": status_resultante,
        "snapshot": oportunidade,
    }).execute()


@router.post("/{oportunidade_id}/arquivar-teste")
def arquivar_teste(oportunidade_id: str, usuario: UsuarioAutenticado = Depends(_admin)):
    registros = supabase.table("cti_oportunidades").select("*").eq("id", oportunidade_id).limit(1).execute().data or []
    if not registros:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")
    atual = registros[0]
    status_anterior = str(atual.get("status") or "OPORTUNIDADE")
    motivo = "Registro criado para teste/homologação"
    payload = {
        "registro_teste": True,
        "arquivado_em": _agora(),
        "arquivado_por": usuario.id,
        "motivo_arquivamento": motivo,
        "status_antes_arquivamento": status_anterior,
        "status": "ARQUIVADO_TESTE",
        "updated_at": _agora(),
    }
    supabase.table("cti_oportunidades").update(payload).eq("id", oportunidade_id).execute()
    arquivado = {**atual, **payload}
    _auditar(arquivado, acao="ARQUIVAR_TESTE", usuario_id=usuario.id, status_anterior=status_anterior, status_resultante="ARQUIVADO_TESTE", motivo=motivo)
    return {"success": True, "oportunidade": arquivado}


@router.get("/testes-arquivados")
def listar_testes_arquivados(usuario: UsuarioAutenticado = Depends(_admin)):
    _ = usuario
    return (
        supabase.table("cti_oportunidades_registros")
        .select("*")
        .eq("registro_teste", True)
        .not_.is_("arquivado_em", "null")
        .order("arquivado_em", desc=True)
        .execute()
        .data
        or []
    )
