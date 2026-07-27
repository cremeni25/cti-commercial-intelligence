from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def obter_usuario_atual(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return {
        "id": usuario.id,
        "auth_id": usuario.auth_id,
        "email": usuario.email,
        "nome": usuario.nome,
        "tipo_usuario": usuario.tipo_usuario,
        "ativo": True,
    }


@router.get("/users")
def listar_usuarios_cti(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente ADMIN_MASTER pode consultar usuários.")

    resposta = (
        supabase.table("cti_users")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resposta.data or []
