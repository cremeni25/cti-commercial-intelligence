from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["auth"])

PerfilCTI = Literal[
    "ADMIN_MASTER",
    "DIRETOR",
    "GESTOR_REGIONAL",
    "VENDEDOR_REGIONAL",
    "GERENTE",
    "VENDEDOR",
]


class UsuarioNovo(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    empresa: str = Field(min_length=2, max_length=120)
    cargo: str = Field(min_length=2, max_length=120)
    tipo_usuario: PerfilCTI
    territorio: str | None = Field(default=None, max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)
    superior_id: str | None = None


class BootstrapAdmin(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    empresa: str = Field(min_length=2, max_length=120)
    cargo: str = Field(min_length=2, max_length=120)
    territorio: str = Field(default="Brasil", min_length=2, max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)


def _dados(resposta):
    return getattr(resposta, "data", None) or []


def _auth_user_id(resposta) -> str:
    usuario = getattr(resposta, "user", None)
    if usuario is None:
        dados = getattr(resposta, "data", None)
        usuario = getattr(dados, "user", None) if dados is not None else None
    auth_id = str(getattr(usuario, "id", "") or "")
    if not auth_id:
        raise RuntimeError("Supabase Auth não retornou o identificador do usuário.")
    return auth_id


def _bootstrap_disponivel() -> bool:
    resposta = supabase.table("cti_users").select("id").limit(1).execute()
    return not bool(_dados(resposta))


def _criar_auth_user(email: str, senha: str, nome: str, tipo_usuario: str) -> str:
    resposta = supabase.auth.admin.create_user(
        {
            "email": email,
            "password": senha,
            "email_confirm": True,
            "user_metadata": {"nome": nome, "tipo_usuario": tipo_usuario},
            "app_metadata": {"role": tipo_usuario},
        }
    )
    return _auth_user_id(resposta)


def _inserir_perfil(auth_id: str, payload: UsuarioNovo | BootstrapAdmin, tipo_usuario: str):
    registro = {
        "auth_id": auth_id,
        "email": str(payload.email).strip().lower(),
        "nome": payload.nome.strip(),
        "empresa": payload.empresa.strip(),
        "cargo": payload.cargo.strip(),
        "tipo_usuario": tipo_usuario,
        "territorio": (payload.territorio or "").strip() or None,
        "ddds": sorted({str(ddd).strip() for ddd in payload.ddds if str(ddd).strip()}),
        "superior_id": getattr(payload, "superior_id", None),
        "ativo": True,
    }
    resposta = supabase.table("cti_users").insert(registro).execute()
    dados = _dados(resposta)
    return dados[0] if dados else registro


@router.get("/bootstrap/status")
def status_bootstrap():
    try:
        return {"disponivel": _bootstrap_disponivel()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Não foi possível verificar o cadastro inicial.") from exc


@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
def criar_primeiro_admin(payload: BootstrapAdmin):
    auth_id = ""
    try:
        if not _bootstrap_disponivel():
            raise HTTPException(status_code=409, detail="O cadastro inicial já foi concluído.")
        auth_id = _criar_auth_user(str(payload.email).lower(), payload.senha, payload.nome, "ADMIN_MASTER")
        perfil = _inserir_perfil(auth_id, payload, "ADMIN_MASTER")
        return {"status": "criado", "usuario": perfil}
    except HTTPException:
        raise
    except Exception as exc:
        if auth_id:
            try:
                supabase.auth.admin.delete_user(auth_id)
            except Exception:
                pass
        raise HTTPException(
            status_code=500,
            detail="Não foi possível criar o ADMIN_MASTER. Confirme a chave service role e a migração de cti_users.",
        ) from exc


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
    resposta = supabase.table("cti_users").select("*").order("created_at", desc=True).execute()
    return _dados(resposta)


@router.post("/users", status_code=status.HTTP_201_CREATED)
def criar_usuario_cti(payload: UsuarioNovo, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente ADMIN_MASTER pode criar usuários.")
    if payload.tipo_usuario == "ADMIN_MASTER":
        raise HTTPException(status_code=400, detail="A criação de outro ADMIN_MASTER exige processo de governança específico.")

    auth_id = ""
    try:
        auth_id = _criar_auth_user(str(payload.email).lower(), payload.senha, payload.nome, payload.tipo_usuario)
        return _inserir_perfil(auth_id, payload, payload.tipo_usuario)
    except Exception as exc:
        if auth_id:
            try:
                supabase.auth.admin.delete_user(auth_id)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Não foi possível criar o usuário CTI.") from exc
