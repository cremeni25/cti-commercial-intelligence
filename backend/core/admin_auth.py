from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.supabase_client import supabase

security = HTTPBearer(auto_error=False)

PERFIS_OFICIAIS = {
    "ADMIN_MASTER",
    "USUARIO_CTI",
    "DIRETOR_VIENA_SP",
    "ADMIN_COMERCIAL_VIENA_SP",
    "ADMIN_FINANCEIRO_VIENA_SP",
    "INDICADOR_VIENA_SP",
    "REPRES_REGIAO_01",
    "REPRES_REGIAO_02",
}
PERFIS_LEGADOS = {
    "DIRETOR": "DIRETOR_VIENA_SP",
    "GESTOR_REGIONAL": "USUARIO_CTI",
    "VENDEDOR_REGIONAL": "USUARIO_CTI",
    "GERENTE": "USUARIO_CTI",
    "VENDEDOR": "USUARIO_CTI",
}
PERFIS_LEITURA_CATALOGO = {"ADMIN_MASTER", "DIRETOR_VIENA_SP", "DIRETOR"}
PERFIS_ESCRITA_CATALOGO = {"ADMIN_MASTER"}


@dataclass(frozen=True)
class UsuarioAutenticado:
    id: str
    auth_id: str
    email: str
    nome: str
    tipo_usuario: str
    permissoes: dict[str, bool] = field(default_factory=dict)


def _extrair_usuario_auth(resposta):
    usuario = getattr(resposta, "user", None)
    if usuario is not None:
        return usuario
    dados = getattr(resposta, "data", None)
    return getattr(dados, "user", None) if dados is not None else None


def _normalizar_perfil(perfil: dict) -> str:
    for chave in ("tipo_usuario", "perfil", "role"):
        texto = str(perfil.get(chave) or "").strip().upper()
        if texto in PERFIS_OFICIAIS:
            return texto
        if texto in PERFIS_LEGADOS:
            return PERFIS_LEGADOS[texto]
    return "USUARIO_CTI" if perfil.get("auth_id") else ""


def _extrair_primeiro_registro(dados) -> dict | None:
    if isinstance(dados, dict):
        return dados
    if isinstance(dados, list) and dados and isinstance(dados[0], dict):
        return dados[0]
    return None


def _executar_busca_perfil(campo: str, valor: str, *, case_insensitive: bool = False) -> dict | None:
    consulta = supabase.table("cti_users").select("*")
    consulta = consulta.ilike(campo, valor) if case_insensitive else consulta.eq(campo, valor)
    return _extrair_primeiro_registro(getattr(consulta.single().execute(), "data", None))


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


def _buscar_permissoes(user_id: str, tipo_usuario: str) -> dict[str, bool]:
    if tipo_usuario == "ADMIN_MASTER":
        return {"acesso_total": True, "usuarios_administrar": True}
    try:
        resposta = supabase.table("cti_user_permissions").select("*").eq("user_id", user_id).single().execute()
        dados = getattr(resposta, "data", None) or {}
        return {chave: bool(valor) for chave, valor in dados.items() if isinstance(valor, bool)}
    except Exception:
        return {}


def usuario_atual(credenciais: HTTPAuthorizationCredentials | None = Depends(security)) -> UsuarioAutenticado:
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticação obrigatória.", headers={"WWW-Authenticate": "Bearer"})
    try:
        auth_user = _extrair_usuario_auth(supabase.auth.get_user(credenciais.credentials))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.") from exc
    auth_id = str(getattr(auth_user, "id", "") or "")
    email = str(getattr(auth_user, "email", "") or "")
    if not auth_id:
        raise HTTPException(status_code=401, detail="Usuário autenticado inválido.")
    perfil = _buscar_perfil(auth_id, email)
    if not perfil or perfil.get("ativo") is False:
        raise HTTPException(status_code=403, detail="Perfil CTI inativo ou inexistente.")
    tipo_usuario = _normalizar_perfil(perfil)
    user_id = str(perfil.get("id") or auth_id)
    return UsuarioAutenticado(
        id=user_id,
        auth_id=auth_id,
        email=str(perfil.get("email") or email),
        nome=str(perfil.get("nome") or email),
        tipo_usuario=tipo_usuario,
        permissoes=_buscar_permissoes(user_id, tipo_usuario),
    )


def exigir_permissao(chave: str):
    def dependencia(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
        if usuario.tipo_usuario == "ADMIN_MASTER" or usuario.permissoes.get("acesso_total") or usuario.permissoes.get(chave):
            return usuario
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário sem permissão para esta operação.")
    return dependencia


def exigir_leitura_catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario in PERFIS_LEITURA_CATALOGO or usuario.permissoes.get("acesso_total"):
        return usuario
    raise HTTPException(status_code=403, detail="Sem permissão para consultar o catálogo.")


def exigir_escrita_catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario in PERFIS_ESCRITA_CATALOGO or usuario.permissoes.get("configuracoes_administrar"):
        return usuario
    raise HTTPException(status_code=403, detail="Sem permissão para alterar o catálogo.")
