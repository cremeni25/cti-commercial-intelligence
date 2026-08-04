from __future__ import annotations

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


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    rows = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not rows:
        raise HTTPException(status_code=404, detail=detalhe)
    return rows[0]


def _normalizar(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.strip().split())
    return value or None


def _contexto(proposta_id: str) -> tuple[dict[str, Any], dict[str, Any], Any, set[str]]:
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada.")
    item_id = str(proposta.get("item_oportunidade_id") or "").strip()
    if not item_id:
        raise HTTPException(status_code=409, detail="A proposta não possui item comercial vinculado.")
    item = _primeiro("cti_oportunidade_itens", item_id, "Item comercial da proposta não encontrado.")
    try:
        definition = document_definition_for_equipment(str(item.get("equipamento") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    fields = {field.code.rsplit(".", 1)[-1] for field in definition.fields}
    return proposta, item, definition, fields


@router.get("/propostas/{proposta_id}/primeira-pagina")
def consultar_primeira_pagina(proposta_id: str):
    proposta, item, definition, fields = _contexto(proposta_id)
    return {
        "proposta_id": proposta_id,
        "item_id": item.get("id"),
        "documento": definition.code,
        "equipamento": definition.equipment,
        "editavel": str(proposta.get("status_documento") or "RASCUNHO") in {"RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"},
        "campos": {
            "voltagem": proposta.get("voltagem") if "voltagem" in fields else None,
            "valor_entrada": proposta.get("valor_entrada"),
            "autorizada_nome_endereco": proposta.get("autorizada_nome_endereco"),
            "lynx_meses": proposta.get("lynx_meses") if "lynx_periodo_meses" in fields else None,
        },
        "aplicabilidade": {
            "voltagem": "voltagem" in fields,
            "valor_entrada": "valor_entrada" in fields,
            "autorizada_nome_endereco": "autorizada_nome_endereco" in fields,
            "lynx_meses": "lynx_periodo_meses" in fields,
        },
    }


@router.put("/propostas/{proposta_id}/primeira-pagina")
def atualizar_primeira_pagina(proposta_id: str, dados: PrimeiraPaginaUpdate):
    proposta, _item, definition, fields = _contexto(proposta_id)
    if str(proposta.get("status_documento") or "RASCUNHO") not in {"RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"}:
        raise HTTPException(status_code=409, detail="Os campos da primeira página só podem ser alterados antes da emissão.")

    supplied = dados.model_dump(exclude_unset=True)
    payload: dict[str, Any] = {}
    if "voltagem" in supplied:
        if "voltagem" not in fields and supplied["voltagem"] not in {None, ""}:
            raise HTTPException(status_code=422, detail="O documento não possui Voltagem na primeira página.")
        payload["voltagem"] = _normalizar(supplied["voltagem"])
    if "valor_entrada" in supplied:
        payload["valor_entrada"] = supplied["valor_entrada"]
    if "autorizada_nome_endereco" in supplied:
        payload["autorizada_nome_endereco"] = _normalizar(supplied["autorizada_nome_endereco"])
    if "lynx_meses" in supplied:
        if "lynx_periodo_meses" not in fields and supplied["lynx_meses"] is not None:
            raise HTTPException(status_code=422, detail="O documento não possui período Lynx Fleet na primeira página.")
        payload["lynx_meses"] = supplied["lynx_meses"]

    updated = supabase.table("cti_propostas").update(payload).eq("id", proposta_id).execute().data or []
    if not updated:
        raise HTTPException(status_code=409, detail="O banco não confirmou a atualização da proposta.")
    return {"ok": True, "documento": definition.code, "campos": {key: updated[0].get(key) for key in ("voltagem", "valor_entrada", "autorizada_nome_endereco", "lynx_meses")}}
