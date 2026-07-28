from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

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
CanalAcesso = Literal["PORTAL", "CRM", "AMBOS"]


class DadosBaseUsuario(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    senha: str = Field(min_length=8, max_length=128)
    empresa: str = Field(min_length=2, max_length=120)
    cargo: str = Field(min_length=2, max_length=120)
    territorio: str | None = Field(default=None, max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        return _normalizar_email(valor)


class UsuarioNovo(DadosBaseUsuario):
    tipo_usuario: PerfilCTI
    superior_id: str | None = None


class BootstrapAdmin(DadosBaseUsuario):
    territorio: str = Field(default="Brasil", min_length=2, max_length=120)


class SolicitacaoAcessoNova(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    telefone: str | None = Field(default=None, max_length=30)
    empresa: str = Field(min_length=2, max_length=120)
    cargo: str = Field(min_length=2, max_length=120)
    canal_solicitado: CanalAcesso = "AMBOS"
    observacoes: str | None = Field(default=None, max_length=1000)

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        return _normalizar_email(valor)


class DecisaoSolicitacao(BaseModel):
    tipo_usuario: PerfilCTI
    territorio: str | None = Field(default=None, max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)
    superior_id: str | None = None
    acesso_portal: bool = True
    acesso_crm: bool = True
    motivo_decisao: str | None = Field(default=None, max_length=1000)


class RejeicaoSolicitacao(BaseModel):
    motivo_decisao: str = Field(min_length=3, max_length=1000)


def _normalizar_email(valor: str) -> str:
    email = valor.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise ValueError("E-mail inválido.")
    return email


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


def _exigir_admin(usuario: UsuarioAutenticado) -> None:
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente ADMIN_MASTER pode executar esta operação.")


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


def _enviar_convite(email: str, nome: str, tipo_usuario: str, acesso_crm: bool) -> str:
    destino = "/crm-app/login" if acesso_crm else "/login"
    resposta = supabase.auth.admin.invite_user_by_email(
        email,
        {
            "redirect_to": f"https://app.cti-intelligence.com/redefinir-senha?destino={destino}",
            "data": {"nome": nome, "tipo_usuario": tipo_usuario},
        },
    )
    return _auth_user_id(resposta)


def _inserir_perfil(auth_id: str, payload: UsuarioNovo | BootstrapAdmin, tipo_usuario: str):
    registro = {
        "auth_id": auth_id,
        "email": payload.email,
        "nome": payload.nome.strip(),
        "empresa": payload.empresa.strip(),
        "cargo": payload.cargo.strip(),
        "tipo_usuario": tipo_usuario,
        "territorio": (payload.territorio or "").strip() or None,
        "ddds": sorted({str(ddd).strip() for ddd in payload.ddds if str(ddd).strip()}),
        "superior_id": getattr(payload, "superior_id", None),
        "ativo": True,
        "status_acesso": "ATIVO",
        "acesso_portal": True,
        "acesso_crm": True,
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
        auth_id = _criar_auth_user(payload.email, payload.senha, payload.nome, "ADMIN_MASTER")
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
        raise HTTPException(status_code=500, detail="Não foi possível criar o ADMIN_MASTER.") from exc


@router.post("/access-requests", status_code=status.HTTP_201_CREATED)
def solicitar_acesso(payload: SolicitacaoAcessoNova):
    try:
        existente = (
            supabase.table("cti_access_requests")
            .select("id,status")
            .eq("email", payload.email)
            .in_("status", ["PENDENTE", "APROVADO", "CONVITE_ENVIADO"])
            .limit(1)
            .execute()
        )
        if _dados(existente):
            raise HTTPException(status_code=409, detail="Já existe uma solicitação ativa para este e-mail.")
        conta = supabase.table("cti_users").select("id").eq("email", payload.email).limit(1).execute()
        if _dados(conta):
            raise HTTPException(status_code=409, detail="Este e-mail já possui cadastro no CTI.")
        registro = {
            "nome": payload.nome.strip(),
            "email": payload.email,
            "telefone": (payload.telefone or "").strip() or None,
            "empresa": payload.empresa.strip(),
            "cargo": payload.cargo.strip(),
            "canal_solicitado": payload.canal_solicitado,
            "observacoes": (payload.observacoes or "").strip() or None,
            "status": "PENDENTE",
        }
        resposta = supabase.table("cti_access_requests").insert(registro).execute()
        dados = _dados(resposta)
        return {"status": "PENDENTE", "solicitacao": dados[0] if dados else registro}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Não foi possível registrar a solicitação de acesso.") from exc


@router.get("/access-requests")
def listar_solicitacoes(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_admin(usuario)
    resposta = supabase.table("cti_access_requests").select("*").order("created_at", desc=True).execute()
    return _dados(resposta)


@router.post("/access-requests/{solicitacao_id}/approve")
def aprovar_solicitacao(
    solicitacao_id: str,
    payload: DecisaoSolicitacao,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_admin(usuario)
    resposta = supabase.table("cti_access_requests").select("*").eq("id", solicitacao_id).single().execute()
    solicitacao = getattr(resposta, "data", None)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    if solicitacao.get("status") != "PENDENTE":
        raise HTTPException(status_code=409, detail="Esta solicitação já foi processada.")
    if not payload.acesso_portal and not payload.acesso_crm:
        raise HTTPException(status_code=400, detail="Libere ao menos um ambiente para o usuário.")

    auth_id = ""
    try:
        auth_id = _enviar_convite(
            solicitacao["email"], solicitacao["nome"], payload.tipo_usuario, payload.acesso_crm
        )
        perfil = {
            "auth_id": auth_id,
            "email": solicitacao["email"],
            "nome": solicitacao["nome"],
            "empresa": solicitacao["empresa"],
            "cargo": solicitacao["cargo"],
            "tipo_usuario": payload.tipo_usuario,
            "territorio": (payload.territorio or "").strip() or None,
            "ddds": sorted({ddd.strip() for ddd in payload.ddds if ddd.strip()}),
            "superior_id": payload.superior_id,
            "ativo": True,
            "status_acesso": "CONVITE_ENVIADO",
            "acesso_portal": payload.acesso_portal,
            "acesso_crm": payload.acesso_crm,
        }
        usuario_criado = supabase.table("cti_users").insert(perfil).execute()
        atualizado = (
            supabase.table("cti_access_requests")
            .update(
                {
                    "status": "CONVITE_ENVIADO",
                    "tipo_usuario": payload.tipo_usuario,
                    "territorio": perfil["territorio"],
                    "ddds": perfil["ddds"],
                    "superior_id": payload.superior_id,
                    "aprovado_por": usuario.id,
                    "decidido_em": "now()",
                    "motivo_decisao": payload.motivo_decisao,
                    "auth_id": auth_id,
                }
            )
            .eq("id", solicitacao_id)
            .execute()
        )
        return {"status": "CONVITE_ENVIADO", "usuario": _dados(usuario_criado), "solicitacao": _dados(atualizado)}
    except Exception as exc:
        if auth_id:
            try:
                supabase.auth.admin.delete_user(auth_id)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Não foi possível aprovar e convidar o usuário.") from exc


@router.post("/access-requests/{solicitacao_id}/reject")
def rejeitar_solicitacao(
    solicitacao_id: str,
    payload: RejeicaoSolicitacao,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_admin(usuario)
    resposta = (
        supabase.table("cti_access_requests")
        .update(
            {
                "status": "REJEITADO",
                "aprovado_por": usuario.id,
                "decidido_em": "now()",
                "motivo_decisao": payload.motivo_decisao,
            }
        )
        .eq("id", solicitacao_id)
        .eq("status", "PENDENTE")
        .execute()
    )
    if not _dados(resposta):
        raise HTTPException(status_code=409, detail="Solicitação inexistente ou já processada.")
    return {"status": "REJEITADO"}


@router.get("/me")
def obter_usuario_atual(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    resposta = supabase.table("cti_users").select("*").eq("id", usuario.id).single().execute()
    return getattr(resposta, "data", None) or {
        "id": usuario.id,
        "auth_id": usuario.auth_id,
        "email": usuario.email,
        "nome": usuario.nome,
        "tipo_usuario": usuario.tipo_usuario,
        "ativo": True,
    }


@router.get("/users")
def listar_usuarios_cti(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_admin(usuario)
    resposta = supabase.table("cti_users").select("*").order("created_at", desc=True).execute()
    return _dados(resposta)


@router.post("/users", status_code=status.HTTP_201_CREATED)
def criar_usuario_cti(payload: UsuarioNovo, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_admin(usuario)
    if payload.tipo_usuario == "ADMIN_MASTER":
        raise HTTPException(status_code=400, detail="A criação de outro ADMIN_MASTER exige governança específica.")
    auth_id = ""
    try:
        auth_id = _criar_auth_user(payload.email, payload.senha, payload.nome, payload.tipo_usuario)
        return _inserir_perfil(auth_id, payload, payload.tipo_usuario)
    except Exception as exc:
        if auth_id:
            try:
                supabase.auth.admin.delete_user(auth_id)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Não foi possível criar o usuário CTI.") from exc
