from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.supabase_client import supabase

security = HTTPBearer(auto_error=False)

PERFIS_OFICIAIS = {
    "ADMIN_MASTER",
    "DIRETOR_VIENA_SP",
    "ADMIN_COMERCIAL_VIENA_SP",
    "ADMIN_FINANCEIRO_VIENA_SP",
    "INDICADOR_VIENA_SP",
    "REPRES_REGIAO_01",
    "REPRES_REGIAO_02",
}

PERFIS_LEGADOS = {
    "DIRETOR": "DIRETOR_VIENA_SP",
    "GESTOR_REGIONAL": "REPRES_REGIAO_01",
    "VENDEDOR_REGIONAL": "REPRES_REGIAO_01",
    "GERENTE": "ADMIN_COMERCIAL_VIENA_SP",
    "VENDEDOR": "REPRES_REGIAO_01",
}

PERFIS_LEITURA_CATALOGO = {"ADMIN_MASTER", "DIRETOR_VIENA_SP"}
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


def _normalizar_perfil(perfil: dict) -> str:
    for chave in ("tipo_usuario", "perfil", "role", "cargo"):
        texto = str(perfil.get(chave) or "").strip().upper()
        if texto in PERFIS_OFICIAIS:
            return texto
        if texto in PERFIS_LEGADOS:
            return PERFIS_LEGADOS[texto]
    return ""


def _extrair_primeiro_registro(dados) -> dict | None:
    if isinstance(dados, dict):
        return dados
    if isinstance(dados, list) and dados:
        primeiro = dados[0]
        return primeiro if isinstance(primeiro, dict) else None
    return None


def _executar_busca_perfil(campo: str, valor: str, *, case_insensitive: bool = False) -> dict | None:
    consulta = supabase.table("cti_users").select("*")
    consulta = consulta.ilike(campo, valor) if case_insensitive else consulta.eq(campo, valor)
    resposta = consulta.single().execute()
    return _extrair_primeiro_registro(getattr(resposta, "data", None))


def _buscar_perfil(auth_id: str, email: str) -> dict | None:
    try:
        perfil = _executar_busca_perfil("auth_id", auth_id)
        if perfil:
            return perfil
    except Exception:
        pass

    if email:
        try:
            return _executar_busca_perfil("email", email, case_insensitive=True)
        except Exception:
            return None
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

    perfil = _buscar_perfil(auth_id, email)
    if not perfil or perfil.get("ativo") is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil CTI inativo ou inexistente.")

    tipo_usuario = _normalizar_perfil(perfil)
    if not tipo_usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil CTI sem permissão definida.")

    return UsuarioAutenticado(
        id=str(perfil.get("id") or auth_id),
        auth_id=auth_id,
        email=str(perfil.get("email") or email),
        nome=str(perfil.get("nome") or perfil.get("email") or email),
        tipo_usuario=tipo_usuario,
    )


def exigir_leitura_catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario not in PERFIS_LEITURA_CATALOGO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para consultar o catálogo.")
    return usuario


def exigir_escrita_catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario not in PERFIS_ESCRITA_CATALOGO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Somente ADMIN_MASTER pode alterar o catálogo.")
    return usuario
