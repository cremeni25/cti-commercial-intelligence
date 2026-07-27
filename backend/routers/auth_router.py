from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual

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
