from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/governanca", tags=["governanca-usuarios"])

PerfilCTI = Literal[
    "ADMIN_MASTER",
    "DIRETOR_VIENA_SP",
    "ADMIN_COMERCIAL_VIENA_SP",
    "ADMIN_FINANCEIRO_VIENA_SP",
    "INDICADOR_VIENA_SP",
    "REPRES_REGIAO_01",
    "REPRES_REGIAO_02",
]


class UsuarioTemporario(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    senha_temporaria: str = Field(min_length=8, max_length=128)
    tipo_usuario: PerfilCTI
    empresa: str = Field(default="VIENA SP", min_length=2, max_length=120)
    territorio: str | None = Field(default="Viena SP", max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        email = valor.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("E-mail inválido.")
        return email


class CadastroComplementar(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    telefone: str = Field(min_length=8, max_length=30)
    cargo: str = Field(min_length=2, max_length=120)
    departamento: str | None = Field(default=None, max_length=120)
    territorio: str | None = Field(default=None, max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)


class ConfirmacaoPrimeiroAcesso(BaseModel):
    cadastro: CadastroComplementar


def _dados(resposta):
    return getattr(resposta, "data", None) or []


def _agora() -> str:
    return datetime.now(UTC).isoformat()


def _exigir_master(usuario: UsuarioAutenticado) -> None:
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Operação exclusiva do ADMIN_MASTER.")


def _permissoes(perfil: str) -> dict:
    return {
        "acesso_portal": True,
        "acesso_crm": True,
        "admin_sistema": perfil == "ADMIN_MASTER",
        "escopo_operacional": "TOTAL" if perfil in {"ADMIN_MASTER", "DIRETOR_VIENA_SP"} else "FUNCAO",
    }


@router.get("/perfis")
def listar_perfis(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    resposta = supabase.table("cti_funcoes").select("*").eq("ativo", True).order("ordem").execute()
    return _dados(resposta)


@router.get("/usuarios")
def listar_usuarios(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    resposta = (
        supabase.table("cti_users")
        .select("*")
        .not_.is_("auth_id", "null")
        .order("created_at", desc=True)
        .execute()
    )
    return _dados(resposta)


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
def criar_usuario(payload: UsuarioTemporario, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    if payload.tipo_usuario == "ADMIN_MASTER":
        raise HTTPException(status_code=400, detail="Não é permitida a criação direta de outro ADMIN_MASTER.")

    existente = supabase.table("cti_users").select("id").eq("email", payload.email).limit(1).execute()
    if _dados(existente):
        raise HTTPException(status_code=409, detail="Já existe usuário com este e-mail.")

    auth_id = ""
    try:
        criado = supabase.auth.admin.create_user(
            {
                "email": payload.email,
                "password": payload.senha_temporaria,
                "email_confirm": True,
                "user_metadata": {
                    "nome": payload.nome.strip(),
                    "tipo_usuario": payload.tipo_usuario,
                    "primeiro_acesso_pendente": True,
                },
                "app_metadata": {"role": payload.tipo_usuario},
            }
        )
        auth_user = getattr(criado, "user", None) or getattr(getattr(criado, "data", None), "user", None)
        auth_id = str(getattr(auth_user, "id", "") or "")
        if not auth_id:
            raise RuntimeError("Supabase Auth não retornou o identificador do usuário.")

        permissoes = _permissoes(payload.tipo_usuario)
        registro = {
            "auth_id": auth_id,
            "nome": payload.nome.strip(),
            "email": payload.email,
            "empresa": payload.empresa.strip(),
            "cargo": payload.tipo_usuario,
            "tipo_usuario": payload.tipo_usuario,
            "territorio": (payload.territorio or "").strip() or None,
            "ddds": sorted({ddd.strip() for ddd in payload.ddds if ddd.strip()}),
            "ativo": True,
            "status_acesso": "PRIMEIRO_ACESSO_PENDENTE",
            "acesso_portal": permissoes["acesso_portal"],
            "acesso_crm": True,
            "primeiro_acesso_pendente": True,
            "cadastro_completo": False,
            "senha_temporaria_criada_em": _agora(),
        }
        resposta = supabase.table("cti_users").insert(registro).execute()
        dados = _dados(resposta)
        return dados[0] if dados else registro
    except HTTPException:
        raise
    except Exception as exc:
        if auth_id:
            try:
                supabase.auth.admin.delete_user(auth_id)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Não foi possível criar o usuário temporário.") from exc


@router.get("/primeiro-acesso/status")
def status_primeiro_acesso(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    resposta = (
        supabase.table("cti_users")
        .select("id,primeiro_acesso_pendente,cadastro_completo,status_acesso,tipo_usuario")
        .eq("id", usuario.id)
        .single()
        .execute()
    )
    dados = getattr(resposta, "data", None) or {}
    return {
        "primeiro_acesso_pendente": bool(dados.get("primeiro_acesso_pendente")),
        "cadastro_completo": bool(dados.get("cadastro_completo")),
        "status_acesso": dados.get("status_acesso"),
        "tipo_usuario": dados.get("tipo_usuario"),
    }


@router.post("/primeiro-acesso/concluir")
def concluir_primeiro_acesso(
    payload: ConfirmacaoPrimeiroAcesso,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    cadastro = payload.cadastro
    atualizacao = {
        "nome": cadastro.nome.strip(),
        "telefone": cadastro.telefone.strip(),
        "cargo": cadastro.cargo.strip(),
        "departamento": (cadastro.departamento or "").strip() or None,
        "territorio": (cadastro.territorio or "").strip() or None,
        "ddds": sorted({ddd.strip() for ddd in cadastro.ddds if ddd.strip()}),
        "primeiro_acesso_pendente": False,
        "cadastro_completo": True,
        "status_acesso": "ATIVO",
        "primeiro_acesso_concluido_em": _agora(),
    }
    resposta = supabase.table("cti_users").update(atualizacao).eq("id", usuario.id).execute()
    dados = _dados(resposta)
    if not dados:
        raise HTTPException(status_code=404, detail="Usuário CTI não encontrado.")
    return dados[0]
