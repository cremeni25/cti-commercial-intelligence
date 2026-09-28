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

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-estabelecimento"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase não configurado")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class EstabelecimentoNegociacaoUpdate(BaseModel):
    cliente_id: str
    motivo: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cliente(cliente_id: str) -> dict:
    registros = supabase.table("clientes").select("*").eq("id", cliente_id).limit(1).execute().data or []
    if not registros:
        raise HTTPException(status_code=404, detail="Estabelecimento/CNPJ não localizado.")
    return registros[0]


def _nome_cliente(cliente: dict) -> str:
    return str(cliente.get("razao_social") or cliente.get("nome") or cliente.get("nome_fantasia") or "Cliente").strip()


@router.put("/oportunidades/{oportunidade_id}/estabelecimento")
def atualizar_estabelecimento_negociacao(
    oportunidade_id: str,
    dados: EstabelecimentoNegociacaoUpdate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    oportunidade = _exigir_acesso(obter_oportunidade(oportunidade_id), usuario)
    novo_cliente_id = str(dados.cliente_id or "").strip()
    if not novo_cliente_id:
        raise HTTPException(status_code=422, detail="Informe o estabelecimento/CNPJ da negociação.")

    cliente_anterior_id = str(oportunidade.get("cliente_id") or "").strip()
    if cliente_anterior_id == novo_cliente_id:
        return {"success": True, "alterado": False, "oportunidade": oportunidade}

    novo_cliente = _cliente(novo_cliente_id)
    cliente_anterior = _cliente(cliente_anterior_id) if cliente_anterior_id else {}

    atualizado = (
        supabase.table("cti_oportunidades_registros")
        .update({"cliente_id": novo_cliente_id, "updated_at": _now()})
        .eq("id", oportunidade_id)
        .execute()
        .data
        or []
    )
    if not atualizado:
        raise HTTPException(status_code=404, detail="Negociação não localizada para atualização.")

    snapshot = {
        "cliente_id_anterior": cliente_anterior_id or None,
        "cliente_nome_anterior": _nome_cliente(cliente_anterior) if cliente_anterior else None,
        "cnpj_anterior": cliente_anterior.get("cnpj") if cliente_anterior else None,
        "cliente_id_novo": novo_cliente_id,
        "cliente_nome_novo": _nome_cliente(novo_cliente),
        "cnpj_novo": novo_cliente.get("cnpj"),
        "motivo": str(dados.motivo or "Alteração de estabelecimento/CNPJ da negociação.").strip(),
    }
    supabase.table("cti_oportunidade_historico").insert({
        "oportunidade_id": oportunidade_id,
        "tipo": "ESTABELECIMENTO",
        "descricao": "Estabelecimento/CNPJ da negociação alterado sem modificar o cadastro mestre nem documentos comerciais já emitidos.",
        "usuario_id": str(usuario.id),
        "payload": snapshot,
        "created_at": _now(),
    }).execute()
    supabase.table("cti_crm_auditoria").insert({
        "entidade": "cti_oportunidades",
        "entidade_id": oportunidade_id,
        "acao": "ALTERACAO_ESTABELECIMENTO_NEGOCIACAO",
        "usuario_id": str(usuario.id),
        "payload": snapshot,
        "created_at": _now(),
    }).execute()
    return {"success": True, "alterado": True, "oportunidade": atualizado[0], "estabelecimento": snapshot}
