from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/governanca", tags=["governanca-usuarios"])


class PermissoesUsuario(BaseModel):
    acesso_portal: bool = False
    acesso_crm: bool = False
    dashboard_executivo: bool = False
    clientes_visualizar: bool = False
    clientes_editar: bool = False
    oportunidades_visualizar: bool = False
    oportunidades_editar: bool = False
    propostas_visualizar: bool = False
    propostas_emitir: bool = False
    pedidos_visualizar: bool = False
    pedidos_converter: bool = False
    pedidos_enviar: bool = False
    financeiro_visualizar: bool = False
    usuarios_administrar: bool = False
    configuracoes_administrar: bool = False
    acesso_total: bool = False


class UsuarioTemporario(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    senha_temporaria: str = Field(min_length=8, max_length=128)
    empresa: str = Field(default="VIENA SP", min_length=2, max_length=120)
    funcao: str = Field(min_length=2, max_length=120)
    territorio: str | None = Field(default=None, max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)
    gestor_responsavel: str | None = Field(default=None, max_length=160)
    permissoes: PermissoesUsuario

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


def _permissoes_dict(payload: PermissoesUsuario) -> dict:
    dados = payload.model_dump()
    if dados["acesso_total"]:
        for chave in dados:
            dados[chave] = True
    dados["updated_at"] = _agora()
    return dados


def _mensagem_excecao(exc: Exception) -> str:
    mensagem = str(exc).strip() or exc.__class__.__name__
    return mensagem[:400]


@router.get("/usuarios")
def listar_usuarios(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    usuarios = _dados(
        supabase.table("cti_users")
        .select("*")
        .not_.is_("auth_id", "null")
        .order("created_at", desc=True)
        .execute()
    )
    permissoes = _dados(supabase.table("cti_user_permissions").select("*").execute())
    por_usuario = {str(item.get("user_id")): item for item in permissoes}
    for item in usuarios:
        item["permissoes"] = por_usuario.get(str(item.get("id")), {})
    return usuarios


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
def criar_usuario(payload: UsuarioTemporario, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    existente = supabase.table("cti_users").select("id").ilike("email", payload.email).limit(1).execute()
    if _dados(existente):
        raise HTTPException(status_code=409, detail="Já existe usuário com este e-mail em cti_users.")

    auth_id = ""
    usuario_cti_id = ""
    etapa = "criação da conta no Supabase Auth"
    try:
        criado = supabase.auth.admin.create_user({
            "email": payload.email,
            "password": payload.senha_temporaria,
            "email_confirm": True,
            "user_metadata": {
                "nome": payload.nome.strip(),
                "funcao": payload.funcao.strip(),
                "primeiro_acesso_pendente": True,
            },
            "app_metadata": {"role": "USUARIO_CTI"},
        })
        auth_user = getattr(criado, "user", None) or getattr(getattr(criado, "data", None), "user", None)
        auth_id = str(getattr(auth_user, "id", "") or "")
        if not auth_id:
            raise RuntimeError("Supabase Auth não retornou o identificador do usuário.")

        etapa = "gravação do cadastro em cti_users"
        registro = {
            "auth_id": auth_id,
            "nome": payload.nome.strip(),
            "email": payload.email,
            "empresa": payload.empresa.strip(),
            "cargo": payload.funcao.strip(),
            "funcao": payload.funcao.strip(),
            "tipo_usuario": "USUARIO_CTI",
            "territorio": (payload.territorio or "").strip() or None,
            "ddds": sorted({ddd.strip() for ddd in payload.ddds if ddd.strip()}),
            "gestor_responsavel": (payload.gestor_responsavel or "").strip() or None,
            "superior_id": None,
            "ativo": True,
            "status_acesso": "PRIMEIRO_ACESSO_PENDENTE",
            "primeiro_acesso_pendente": True,
            "cadastro_completo": False,
            "senha_temporaria_criada_em": _agora(),
        }
        resposta = supabase.table("cti_users").insert(registro).execute()
        dados = _dados(resposta)
        if not dados:
            raise RuntimeError("O banco não retornou o perfil CTI criado.")
        criado_cti = dados[0]
        usuario_cti_id = str(criado_cti.get("id") or "")
        if not usuario_cti_id:
            raise RuntimeError("O perfil CTI foi criado sem identificador.")

        etapa = "gravação das permissões individuais"
        permissoes = {"user_id": usuario_cti_id, **_permissoes_dict(payload.permissoes)}
        resposta_permissoes = supabase.table("cti_user_permissions").insert(permissoes).execute()
        if not _dados(resposta_permissoes):
            raise RuntimeError("O banco não confirmou a gravação das permissões.")

        criado_cti["permissoes"] = permissoes
        return criado_cti
    except HTTPException:
        raise
    except Exception as exc:
        if usuario_cti_id:
            try:
                supabase.table("cti_user_permissions").delete().eq("user_id", usuario_cti_id).execute()
            except Exception:
                pass
            try:
                supabase.table("cti_users").delete().eq("id", usuario_cti_id).execute()
            except Exception:
                pass
        if auth_id:
            try:
                supabase.auth.admin.delete_user(auth_id)
            except Exception:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível criar o usuário na etapa '{etapa}': {_mensagem_excecao(exc)}",
        ) from exc


@router.put("/usuarios/{usuario_id}/permissoes")
def atualizar_permissoes(usuario_id: str, payload: PermissoesUsuario, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    dados = {"user_id": usuario_id, **_permissoes_dict(payload)}
    resposta = supabase.table("cti_user_permissions").upsert(dados, on_conflict="user_id").execute()
    return _dados(resposta)[0] if _dados(resposta) else dados


@router.get("/primeiro-acesso/status")
def status_primeiro_acesso(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    resposta = supabase.table("cti_users").select("id,primeiro_acesso_pendente,cadastro_completo,status_acesso,tipo_usuario").eq("id", usuario.id).single().execute()
    dados = getattr(resposta, "data", None) or {}
    return {
        "primeiro_acesso_pendente": bool(dados.get("primeiro_acesso_pendente")),
        "cadastro_completo": bool(dados.get("cadastro_completo")),
        "status_acesso": dados.get("status_acesso"),
        "tipo_usuario": dados.get("tipo_usuario"),
    }


@router.post("/primeiro-acesso/concluir")
def concluir_primeiro_acesso(payload: ConfirmacaoPrimeiroAcesso, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    cadastro = payload.cadastro
    atualizacao = {
        "nome": cadastro.nome.strip(),
        "telefone": cadastro.telefone.strip(),
        "cargo": cadastro.cargo.strip(),
        "funcao": cadastro.cargo.strip(),
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
