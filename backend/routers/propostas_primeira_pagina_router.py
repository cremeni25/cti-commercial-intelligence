from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase
from services.proposal_document_definitions import document_definition_for_equipment

router = APIRouter(prefix="/crm-documentos", tags=["Propostas - primeira página"])


class PrimeiraPaginaUpdate(BaseModel):
    voltagem: str | None = None
    valor_entrada: float | None = Field(default=None, ge=0)
    autorizada_nome_endereco: str | None = None
    lynx_meses: int | None = Field(default=None, ge=0)


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    try:
        rows = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao consultar {tabela}: {exc}") from exc
    if not rows:
        raise HTTPException(status_code=404, detail=detalhe)
    return rows[0]


def _normalizar_texto(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


@router.get("/propostas/{proposta_id}/primeira-pagina")
def consultar_primeira_pagina(proposta_id: str):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada.")
    item_id = str(proposta.get("item_oportunidade_id") or "").strip()
    if not item_id:
        raise HTTPException(status_code=409, detail="A proposta não possui item comercial vinculado.")
    item = _primeiro("cti_oportunidade_itens", item_id, "Item comercial da proposta não encontrado.")
    try:
        definition = document_definition_for_equipment(str(item.get("equipamento") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    field_names = {field.code.rsplit(".", 1)[-1] for field in definition.fields}
    return {
        "proposta_id": proposta_id,
        "item_id": item_id,
        "documento": definition.code,
        "equipamento": definition.equipment,
        "campos": {
            "voltagem": item.get("voltagem") if "voltagem" in field_names else None,
            "valor_entrada": item.get("valor_entrada"),
            "autorizada_nome_endereco": item.get("autorizada_nome_endereco"),
            "lynx_meses": item.get("lynx_meses") if "lynx_periodo_meses" in field_names else None,
        },
        "aplicabilidade": {
            "voltagem": "voltagem" in field_names,
            "valor_entrada": "valor_entrada" in field_names,
            "autorizada_nome_endereco": "autorizada_nome_endereco" in field_names,
            "lynx_meses": "lynx_periodo_meses" in field_names,
        },
    }


@router.put("/propostas/{proposta_id}/primeira-pagina")
def atualizar_primeira_pagina(proposta_id: str, dados: PrimeiraPaginaUpdate):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada.")
    if str(proposta.get("status_documento") or "RASCUNHO") not in {"RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"}:
        raise HTTPException(status_code=409, detail="Os campos da primeira página só podem ser alterados antes da emissão.")

    item_id = str(proposta.get("item_oportunidade_id") or "").strip()
    if not item_id:
        raise HTTPException(status_code=409, detail="A proposta não possui item comercial vinculado.")
    item = _primeiro("cti_oportunidade_itens", item_id, "Item comercial da proposta não encontrado.")
    try:
        definition = document_definition_for_equipment(str(item.get("equipamento") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    field_names = {field.code.rsplit(".", 1)[-1] for field in definition.fields}
    supplied = dados.model_dump(exclude_unset=True)
    payload: dict[str, Any] = {"updated_at": _agora()}

    if "voltagem" in supplied:
        if "voltagem" not in field_names and supplied["voltagem"] not in {None, ""}:
            raise HTTPException(status_code=422, detail="O documento selecionado não possui campo Voltagem na primeira página.")
        payload["voltagem"] = _normalizar_texto(supplied["voltagem"])

    if "valor_entrada" in supplied:
        payload["valor_entrada"] = supplied["valor_entrada"]

    if "autorizada_nome_endereco" in supplied:
        payload["autorizada_nome_endereco"] = _normalizar_texto(supplied["autorizada_nome_endereco"])

    if "lynx_meses" in supplied:
        if "lynx_periodo_meses" not in field_names and supplied["lynx_meses"] is not None:
            raise HTTPException(status_code=422, detail="O documento selecionado não possui período Lynx Fleet na primeira página.")
        payload["lynx_meses"] = supplied["lynx_meses"]

    try:
        updated = supabase.table("cti_oportunidade_itens").update(payload).eq("id", item_id).execute().data or []
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao salvar os campos da primeira página: {exc}") from exc
    if not updated:
        raise HTTPException(status_code=409, detail="O banco não confirmou a atualização dos campos da proposta.")

    return {
        "ok": True,
        "proposta_id": proposta_id,
        "item_id": item_id,
        "documento": definition.code,
        "campos": {
            "voltagem": updated[0].get("voltagem"),
            "valor_entrada": updated[0].get("valor_entrada"),
            "autorizada_nome_endereco": updated[0].get("autorizada_nome_endereco"),
            "lynx_meses": updated[0].get("lynx_meses"),
        },
    }
