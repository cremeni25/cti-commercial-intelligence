from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_router import _exigir_acesso
from routers.crm_router import obter_oportunidade
from services.cnpj_enrichment_service import consultar_cnpj_publico, somente_digitos

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-estabelecimento"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase não configurado")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class EstabelecimentoNegociacaoUpdate(BaseModel):
    cliente_id: str
    motivo: Optional[str] = None


class NovoEstabelecimentoGrupo(BaseModel):
    cnpj: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cliente(cliente_id: str) -> dict:
    registros = supabase.table("clientes").select("*").eq("id", cliente_id).limit(1).execute().data or []
    if not registros:
        raise HTTPException(status_code=404, detail="Estabelecimento/CNPJ não localizado.")
    return registros[0]


def _nome_cliente(cliente: dict) -> str:
    return str(cliente.get("razao_social") or cliente.get("nome") or cliente.get("nome_fantasia") or "Cliente").strip()


def _vincular(grupo_id: str, estabelecimento_id: str, usuario_id: str) -> None:
    existente = supabase.table("cti_grupo_estabelecimentos").select("id").eq("grupo_cliente_id", grupo_id).eq("estabelecimento_cliente_id", estabelecimento_id).limit(1).execute().data or []
    if not existente:
        supabase.table("cti_grupo_estabelecimentos").insert({"grupo_cliente_id": grupo_id, "estabelecimento_cliente_id": estabelecimento_id, "criado_por": usuario_id}).execute()


@router.get("/oportunidades/{oportunidade_id}/estabelecimentos")
def listar_estabelecimentos_negociacao(oportunidade_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    oportunidade = _exigir_acesso(obter_oportunidade(oportunidade_id), usuario)
    atual_id = str(oportunidade.get("cliente_id") or "").strip()
    if not atual_id:
        return {"grupo_cliente_id": None, "estabelecimentos": []}

    # Se o estabelecimento atual já pertence a um grupo, preserva o grupo original.
    vinculo = supabase.table("cti_grupo_estabelecimentos").select("grupo_cliente_id").eq("estabelecimento_cliente_id", atual_id).limit(1).execute().data or []
    grupo_id = str(vinculo[0].get("grupo_cliente_id")) if vinculo else atual_id
    _vincular(grupo_id, grupo_id, str(usuario.id))

    vinculos = supabase.table("cti_grupo_estabelecimentos").select("estabelecimento_cliente_id").eq("grupo_cliente_id", grupo_id).execute().data or []
    ids = [str(item.get("estabelecimento_cliente_id")) for item in vinculos if item.get("estabelecimento_cliente_id")]
    estabelecimentos = []
    for estabelecimento_id in ids:
        try:
            item = _cliente(estabelecimento_id)
            estabelecimentos.append(item)
        except HTTPException:
            continue
    return {"grupo_cliente_id": grupo_id, "grupo": _cliente(grupo_id), "estabelecimentos": estabelecimentos}


@router.post("/oportunidades/{oportunidade_id}/estabelecimentos")
def adicionar_estabelecimento_grupo(oportunidade_id: str, dados: NovoEstabelecimentoGrupo, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    oportunidade = _exigir_acesso(obter_oportunidade(oportunidade_id), usuario)
    atual_id = str(oportunidade.get("cliente_id") or "").strip()
    if not atual_id:
        raise HTTPException(status_code=422, detail="Negociação sem cliente vinculado.")

    vinculo = supabase.table("cti_grupo_estabelecimentos").select("grupo_cliente_id").eq("estabelecimento_cliente_id", atual_id).limit(1).execute().data or []
    grupo_id = str(vinculo[0].get("grupo_cliente_id")) if vinculo else atual_id
    _vincular(grupo_id, grupo_id, str(usuario.id))

    cnpj = somente_digitos(dados.cnpj)
    existente = supabase.table("clientes").select("*").eq("cnpj", cnpj).limit(1).execute().data or []
    if existente:
        estabelecimento = existente[0]
    else:
        consulta = consultar_cnpj_publico(cnpj)
        if not consulta.get("ok"):
            tipo = consulta.get("tipo")
            codigo = 422 if tipo == "CNPJ_INVALIDO" else 404 if tipo == "NAO_ENCONTRADO" else 503
            raise HTTPException(status_code=codigo, detail=consulta.get("detail") or "Não foi possível consultar o CNPJ.")
        cadastral = consulta["dados"]
        payload = {
            "nome": cadastral.get("nome") or cadastral.get("nome_fantasia") or cnpj,
            "cnpj": cnpj,
            "cidade": cadastral.get("cidade"),
            "estado": cadastral.get("estado"),
            "inscricao_estadual": cadastral.get("inscricao_estadual"),
            "endereco": cadastral.get("endereco"),
            "numero": cadastral.get("numero"),
            "complemento": cadastral.get("complemento"),
            "bairro": cadastral.get("bairro"),
            "cep": cadastral.get("cep"),
            "fone": cadastral.get("fone"),
            "email": cadastral.get("email"),
            "ddd": cadastral.get("ddd"),
            "status": "ATIVO",
        }
        criado = supabase.table("clientes").insert(payload).execute().data or []
        if not criado:
            raise HTTPException(status_code=500, detail="Não foi possível cadastrar o estabelecimento.")
        estabelecimento = criado[0]

    _vincular(grupo_id, str(estabelecimento["id"]), str(usuario.id))
    return {"success": True, "grupo_cliente_id": grupo_id, "estabelecimento": estabelecimento}


@router.put("/oportunidades/{oportunidade_id}/estabelecimento")
def atualizar_estabelecimento_negociacao(oportunidade_id: str, dados: EstabelecimentoNegociacaoUpdate, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    oportunidade = _exigir_acesso(obter_oportunidade(oportunidade_id), usuario)
    novo_cliente_id = str(dados.cliente_id or "").strip()
    if not novo_cliente_id:
        raise HTTPException(status_code=422, detail="Informe o estabelecimento/CNPJ da negociação.")

    cliente_anterior_id = str(oportunidade.get("cliente_id") or "").strip()
    if cliente_anterior_id == novo_cliente_id:
        return {"success": True, "alterado": False, "oportunidade": oportunidade}

    # Segurança: só permite selecionar CNPJ pertencente ao grupo da negociação.
    vinculo_atual = supabase.table("cti_grupo_estabelecimentos").select("grupo_cliente_id").eq("estabelecimento_cliente_id", cliente_anterior_id).limit(1).execute().data or []
    grupo_id = str(vinculo_atual[0].get("grupo_cliente_id")) if vinculo_atual else cliente_anterior_id
    permitido = supabase.table("cti_grupo_estabelecimentos").select("id").eq("grupo_cliente_id", grupo_id).eq("estabelecimento_cliente_id", novo_cliente_id).limit(1).execute().data or []
    if not permitido:
        raise HTTPException(status_code=422, detail="O CNPJ selecionado não pertence ao grupo econômico desta negociação.")

    novo_cliente = _cliente(novo_cliente_id)
    cliente_anterior = _cliente(cliente_anterior_id) if cliente_anterior_id else {}
    atualizado = supabase.table("cti_oportunidades_registros").update({"cliente_id": novo_cliente_id, "updated_at": _now()}).eq("id", oportunidade_id).execute().data or []
    if not atualizado:
        raise HTTPException(status_code=404, detail="Negociação não localizada para atualização.")

    snapshot = {"grupo_cliente_id": grupo_id, "cliente_id_anterior": cliente_anterior_id or None, "cliente_nome_anterior": _nome_cliente(cliente_anterior) if cliente_anterior else None, "cnpj_anterior": cliente_anterior.get("cnpj") if cliente_anterior else None, "cliente_id_novo": novo_cliente_id, "cliente_nome_novo": _nome_cliente(novo_cliente), "cnpj_novo": novo_cliente.get("cnpj"), "motivo": str(dados.motivo or "Alteração de estabelecimento/CNPJ da negociação.").strip()}
    supabase.table("cti_oportunidade_historico").insert({"oportunidade_id": oportunidade_id, "tipo": "ESTABELECIMENTO", "descricao": "Estabelecimento/CNPJ da negociação alterado sem modificar o cadastro mestre nem documentos comerciais já emitidos.", "usuario_id": str(usuario.id), "payload": snapshot, "created_at": _now()}).execute()
    supabase.table("cti_crm_auditoria").insert({"entidade": "cti_oportunidades", "entidade_id": oportunidade_id, "acao": "ALTERACAO_ESTABELECIMENTO_NEGOCIACAO", "usuario_id": str(usuario.id), "payload": snapshot, "created_at": _now()}).execute()
    return {"success": True, "alterado": True, "oportunidade": atualizado[0], "estabelecimento": snapshot}
