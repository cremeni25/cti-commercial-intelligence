from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.supabase_client import supabase

security = HTTPBearer(auto_error=False)

PERFIS_LEITURA_CATALOGO = {"ADMIN_MASTER", "DIRETOR"}
PERFIS_ESCRITA_CATALOGO = {"ADMIN_MASTER"}


@dataclass(frozen=True)
class UsuarioAutenticado:
    id: str
    auth_id: str
    email: str
    nome: str
    tipo_usuario: str


def _extrair_usuario_auth(resposta):
    usuario = getattr(resposta, "user", None)
    if usuario is not None:
        return usuario
    dados = getattr(resposta, "data", None)
    if dados is not None:
        return getattr(dados, "user", None)
    return None


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(security),
) -> UsuarioAutenticado:
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        resposta_auth = supabase.auth.get_user(credenciais.credentials)
        auth_user = _extrair_usuario_auth(resposta_auth)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    auth_id = str(getattr(auth_user, "id", "") or "")
    email = str(getattr(auth_user, "email", "") or "")
    if not auth_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário autenticado inválido.")

    try:
        perfil = (
            supabase.table("cti_users")
            .select("id,auth_id,nome,email,tipo_usuario,ativo")
            .eq("auth_id", auth_id)
            .single()
            .execute()
            .data
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil CTI não autorizado.") from exc

    if not perfil or not perfil.get("ativo", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil CTI inativo ou inexistente.")

    return UsuarioAutenticado(
        id=str(perfil.get("id") or ""),
        auth_id=auth_id,
        email=str(perfil.get("email") or email),
        nome=str(perfil.get("nome") or perfil.get("email") or email),
        tipo_usuario=str(perfil.get("tipo_usuario") or "").upper(),
    )


def exigir_leitura_catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario not in PERFIS_LEITURA_CATALOGO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para consultar o catálogo.")
    return usuario


def exigir_escrita_catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario not in PERFIS_ESCRITA_CATALOGO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Somente ADMIN_MASTER pode alterar o catálogo.")
    return usuario
