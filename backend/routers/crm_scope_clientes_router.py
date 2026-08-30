from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.clientes_oportunidade_router import ClienteCreate, criar_cliente_crm_app, listar_clientes_crm_app
from routers.crm_app_clientes_edicao_router import ClienteEdicao, atualizar_cliente_crm_app, obter_cliente_crm_app

router = APIRouter(prefix="/crm-seguro/clientes", tags=["crm-seguro-clientes"])
PERFIS_REGIONAIS = {"REPRES_REGIAO_01", "REPRES_REGIAO_02", "INDICADOR_VIENA_SP"}


class ResponsabilidadeCliente(BaseModel):
    responsavel_id: Optional[str] = None
    conta_direta_master: bool = False
    restaurar_territorio: bool = False
    motivo: Optional[str] = None


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fold(valor: Any) -> str:
    texto = str(valor or "").strip().upper()
    tabela = str.maketrans("ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ", "AAAAAEEEEIIIIOOOOOUUUUC")
    return re.sub(r"\s+", " ", texto.translate(tabela))


def _codigo_regional(valor: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", _fold(valor))


def _visao_total(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP"
        and bool(usuario.permissoes.get("acesso_total"))
    )


def _exigir_master(usuario: UsuarioAutenticado) -> None:
    if _visao_total(usuario):
        return
    raise HTTPException(status_code=403, detail="Somente usuários Master podem alterar a responsabilidade comercial de clientes.")


def _exigir_permissao(usuario: UsuarioAutenticado, permissao: str) -> None:
    if _visao_total(usuario) or bool(usuario.permissoes.get(permissao)):
        return
    raise HTTPException(status_code=403, detail="Usuário sem permissão para esta operação cadastral.")


def _perfil_usuario(usuario_id: str) -> dict[str, Any]:
    dados = (
        supabase.table("cti_users")
        .select("id,nome,tipo_usuario,codigo_regional,ddds,ativo")
        .eq("id", usuario_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    return dados[0] if dados else {}


def _cliente_no_escopo(cliente: dict[str, Any], usuario: UsuarioAutenticado) -> bool:
    if _visao_total(usuario):
        return True
    if usuario.tipo_usuario not in PERFIS_REGIONAIS:
        return True
    responsavel = str(cliente.get("responsavel_comercial_id") or "")
    if responsavel:
        return responsavel == str(usuario.id)
    perfil = _perfil_usuario(str(usuario.id))
    codigo_usuario = _codigo_regional(perfil.get("codigo_regional"))
    codigo_cliente = _codigo_regional(cliente.get("sub_regiao"))
    return bool(codigo_usuario and codigo_cliente and codigo_usuario == codigo_cliente)


def _clientes_filtrados(usuario: UsuarioAutenticado, responsavel_id: str | None = None) -> list[dict[str, Any]]:
    base = listar_clientes_crm_app()
    if _visao_total(usuario):
        if responsavel_id:
            return [item for item in base if str(item.get("responsavel_comercial_id") or "") == str(responsavel_id)]
        return base
    return [item for item in base if _cliente_no_escopo(item, usuario)]


def _anotar_responsavel(item: dict[str, Any]) -> dict[str, Any]:
    responsavel_id = str(item.get("responsavel_comercial_id") or "")
    if not responsavel_id:
        return item
    perfil = _perfil_usuario(responsavel_id)
    return {**item,"responsavel_comercial_nome": perfil.get("nome"),"responsavel_comercial_tipo": perfil.get("tipo_usuario")}


def _responsavel_territorial(cliente: dict[str, Any]) -> dict[str, Any] | None:
    codigo = _codigo_regional(cliente.get("sub_regiao"))
    if codigo not in {"REGIAO01", "REGIAO02"}:
        return None
    esperado = "REGIAO 01" if codigo == "REGIAO01" else "REGIAO 02"
    dados = (
        supabase.table("cti_users")
        .select("id,nome,tipo_usuario,codigo_regional,ativo")
        .eq("codigo_regional", esperado)
        .eq("ativo", True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return dados[0] if dados else None


def _registrar_historico(cliente_id: str, anterior_id: str | None, novo_id: str | None, tipo_anterior: str | None, tipo_novo: str, motivo: str | None, alterado_por: str) -> None:
    supabase.table("cti_cliente_responsabilidade_historico").insert({
        "cliente_id": cliente_id,"responsavel_anterior_id": anterior_id,"responsavel_novo_id": novo_id,
        "tipo_anterior": tipo_anterior,"tipo_novo": tipo_novo,"motivo": motivo,"alterado_por": alterado_por,
    }).execute()


@router.get("/responsaveis")
def listar_responsaveis_comerciais(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    usuarios = supabase.table("cti_users").select("id,nome,email,tipo_usuario,codigo_regional,ddds,ativo").eq("ativo", True).execute().data or []
    permitidos = {"ADMIN_MASTER","DIRETOR_VIENA_SP","REPRES_REGIAO_01","REPRES_REGIAO_02","INDICADOR_VIENA_SP"}
    return sorted([item for item in usuarios if str(item.get("tipo_usuario") or "").upper() in permitidos], key=lambda item: str(item.get("nome") or "").casefold())


@router.get("")
def listar_clientes_seguro(responsavel_id: str | None = Query(default=None), usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_permissao(usuario, "clientes_visualizar")
    if responsavel_id and not _visao_total(usuario):
        raise HTTPException(status_code=403, detail="Filtro por outro responsável disponível somente para usuários Master.")
    return [_anotar_responsavel(item) for item in _clientes_filtrados(usuario, responsavel_id)]


@router.post("")
def criar_cliente_seguro(dados: ClienteCreate, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_permissao(usuario, "clientes_editar")
    resposta = criar_cliente_crm_app(dados)
    cliente = resposta.get("cliente") or {}
    cliente_id = str(cliente.get("id") or "")
    if cliente_id and usuario.tipo_usuario in PERFIS_REGIONAIS and not _visao_total(usuario):
        supabase.table("clientes").update({
            "responsavel_comercial_id": str(usuario.id),"responsabilidade_tipo": "TERRITORIO",
            "responsabilidade_atualizada_em": _agora(),"responsabilidade_atualizada_por": str(usuario.id),
        }).eq("id", cliente_id).execute()
        resposta["cliente"] = obter_cliente_crm_app(cliente_id)
    return resposta


@router.get("/{cliente_id}")
def obter_cliente_seguro(cliente_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_permissao(usuario, "clientes_visualizar")
    cliente = obter_cliente_crm_app(cliente_id)
    if not _cliente_no_escopo(cliente, usuario):
        raise HTTPException(status_code=403, detail="Cliente fora do seu escopo comercial.")
    return _anotar_responsavel(cliente)


@router.put("/{cliente_id}")
def atualizar_cliente_seguro(cliente_id: str, dados: ClienteEdicao, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_permissao(usuario, "clientes_editar")
    if _visao_total(usuario):
        return atualizar_cliente_crm_app(cliente_id, dados)
    atual = obter_cliente_crm_app(cliente_id)
    if not _cliente_no_escopo(atual, usuario):
        raise HTTPException(status_code=403, detail="Cliente fora do seu escopo comercial.")
    return atualizar_cliente_crm_app(cliente_id, dados)


@router.put("/{cliente_id}/responsavel")
def definir_responsabilidade_cliente(cliente_id: str, dados: ResponsabilidadeCliente, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_master(usuario)
    cliente = obter_cliente_crm_app(cliente_id)
    anterior_id = str(cliente.get("responsavel_comercial_id") or "") or None
    tipo_anterior = str(cliente.get("responsabilidade_tipo") or "TERRITORIO")
    if dados.restaurar_territorio:
        territorial = _responsavel_territorial(cliente)
        novo_id = str(territorial.get("id")) if territorial else None
        tipo_novo = "TERRITORIO"
    else:
        if not dados.responsavel_id:
            raise HTTPException(status_code=422, detail="Informe o responsável comercial.")
        perfil = _perfil_usuario(str(dados.responsavel_id))
        if not perfil or perfil.get("ativo") is False:
            raise HTTPException(status_code=422, detail="Responsável comercial inválido ou inativo.")
        novo_id = str(perfil["id"])
        tipo_novo = "CONTA_DIRETA_MASTER" if dados.conta_direta_master else "ATRIBUICAO_MASTER"
    supabase.table("clientes").update({
        "responsavel_comercial_id": novo_id,"responsabilidade_tipo": tipo_novo,
        "responsabilidade_atualizada_em": _agora(),"responsabilidade_atualizada_por": str(usuario.id),
    }).eq("id", cliente_id).execute()
    _registrar_historico(cliente_id, anterior_id, novo_id, tipo_anterior, tipo_novo, dados.motivo, str(usuario.id))
    return _anotar_responsavel(obter_cliente_crm_app(cliente_id))
