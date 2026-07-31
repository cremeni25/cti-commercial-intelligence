from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-documentos", tags=["CRM Documentos Comerciais"])


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail=detalhe)
    return dados[0]


@router.get("/propostas/{proposta_id}")
def consultar_proposta(proposta_id: str):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada")
    item = None
    oportunidade = None
    cliente = None
    aceites: list[dict[str, Any]] = []
    pedidos: list[dict[str, Any]] = []

    if proposta.get("item_oportunidade_id"):
        item = _primeiro("cti_oportunidade_itens", str(proposta["item_oportunidade_id"]), "Item da oportunidade não encontrado")
    if proposta.get("oportunidade_id"):
        oportunidade = _primeiro("cti_oportunidades", str(proposta["oportunidade_id"]), "Oportunidade não encontrada")
    if proposta.get("cliente_id"):
        clientes = supabase.table("cti_clientes").select("*").eq("id", proposta["cliente_id"]).limit(1).execute().data or []
        cliente = clientes[0] if clientes else None

    aceites = supabase.table("cti_proposta_aceites").select("*").eq("proposta_id", proposta_id).order("solicitado_em", desc=True).execute().data or []
    pedidos = supabase.table("cti_pedidos").select("*").eq("proposta_aceita_id", proposta_id).order("created_at", desc=True).execute().data or []

    return {
        "proposta": proposta,
        "item": item,
        "oportunidade": oportunidade,
        "cliente": cliente,
        "aceites": aceites,
        "pedidos": pedidos,
    }


@router.get("/aceites/{aceite_id}/publico")
def consultar_aceite_publico(aceite_id: str):
    aceite = _primeiro("cti_proposta_aceites", aceite_id, "Solicitação de aceite não encontrada")
    proposta = _primeiro("cti_propostas", str(aceite["proposta_id"]), "Proposta não encontrada")
    item = _primeiro("cti_oportunidade_itens", str(proposta["item_oportunidade_id"]), "Item da oportunidade não encontrado") if proposta.get("item_oportunidade_id") else None
    oportunidade = _primeiro("cti_oportunidades", str(proposta["oportunidade_id"]), "Oportunidade não encontrada") if proposta.get("oportunidade_id") else None

    if aceite.get("status") == "PENDENTE":
        supabase.table("cti_proposta_aceites").update({"status": "VISUALIZADO", "visualizado_em": _agora()}).eq("id", aceite_id).execute()
        aceite = {**aceite, "status": "VISUALIZADO", "visualizado_em": _agora()}
    if proposta.get("status_documento") in {"EMITIDA", "ENVIADA"}:
        supabase.table("cti_propostas").update({"status_documento": "VISUALIZADA", "updated_at": _agora()}).eq("id", proposta["id"]).execute()
        proposta = {**proposta, "status_documento": "VISUALIZADA"}

    return {
        "aceite": {
            "id": aceite.get("id"),
            "metodo": aceite.get("metodo"),
            "nome_signatario": aceite.get("nome_signatario"),
            "documento_signatario": aceite.get("documento_signatario"),
            "email_signatario": aceite.get("email_signatario"),
            "telefone_signatario": aceite.get("telefone_signatario"),
            "status": aceite.get("status"),
            "solicitado_em": aceite.get("solicitado_em"),
            "aceito_em": aceite.get("aceito_em"),
        },
        "proposta": proposta,
        "item": item,
        "oportunidade": oportunidade,
    }
