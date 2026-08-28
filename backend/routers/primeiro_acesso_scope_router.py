from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.governanca_usuarios_router import _agora, _dados

router = APIRouter(prefix="/governanca/primeiro-acesso", tags=["primeiro-acesso-seguro"])


class CadastroPessoalPrimeiroAcesso(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    telefone: str = Field(min_length=8, max_length=30)
    cargo: str = Field(min_length=2, max_length=120)
    departamento: str | None = Field(default=None, max_length=120)
    # Mantidos no contrato por compatibilidade com clientes já publicados, mas ignorados.
    # Território e DDDs são governança administrativa e não podem ser redefinidos pelo usuário.
    territorio: str | None = Field(default=None, max_length=120)
    ddds: list[str] = Field(default_factory=list, max_length=20)


class ConfirmacaoPrimeiroAcessoSeguro(BaseModel):
    cadastro: CadastroPessoalPrimeiroAcesso


@router.get("/status")
def status_primeiro_acesso_seguro(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    resposta = (
        supabase.table("cti_users")
        .select("id,primeiro_acesso_pendente,cadastro_completo,status_acesso,tipo_usuario,territorio,ddds")
        .eq("id", usuario.id)
        .single()
        .execute()
    )
    dados = getattr(resposta, "data", None) or {}
    if not dados:
        raise HTTPException(status_code=404, detail="Usuário CTI não encontrado.")
    return {
        "primeiro_acesso_pendente": bool(dados.get("primeiro_acesso_pendente")),
        "cadastro_completo": bool(dados.get("cadastro_completo")),
        "status_acesso": dados.get("status_acesso"),
        "tipo_usuario": dados.get("tipo_usuario"),
        "territorio": dados.get("territorio"),
        "ddds": dados.get("ddds") or [],
    }


@router.post("/concluir")
def concluir_primeiro_acesso_seguro(
    payload: ConfirmacaoPrimeiroAcessoSeguro,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    cadastro = payload.cadastro
    atualizacao = {
        "nome": cadastro.nome.strip(),
        "telefone": cadastro.telefone.strip(),
        "cargo": cadastro.cargo.strip(),
        "funcao": cadastro.cargo.strip(),
        "departamento": (cadastro.departamento or "").strip() or None,
        # NÃO atualizar territorio, ddds, tipo_usuario ou permissões aqui.
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
