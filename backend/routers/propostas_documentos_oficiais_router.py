from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase
from services.proposal_document_preview import preview_official_proposal
from services.proposal_document_repository import (
    FINAL_BUCKET,
    ProposalDocumentRepositoryError,
    finalize_official_proposal,
)

router = APIRouter(prefix="/crm-documentos", tags=["Propostas oficiais Carrier"])


def _first(table: str, record_id: str, detail: str) -> dict[str, Any]:
    rows = supabase.table(table).select("*").eq("id", record_id).limit(1).execute().data or []
    if not rows:
        raise HTTPException(status_code=404, detail=detail)
    return rows[0]


def _proposal_package(proposal_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    proposal = _first("cti_propostas", proposal_id, "Proposta não encontrada.")
    item_id = str(proposal.get("item_oportunidade_id") or "").strip()
    opportunity_id = str(proposal.get("oportunidade_id") or "").strip()
    client_id = str(proposal.get("cliente_id") or "").strip()
    if not item_id or not opportunity_id or not client_id:
        raise HTTPException(status_code=409, detail="A proposta não possui todos os vínculos documentais obrigatórios.")
    item = _first("cti_oportunidade_itens", item_id, "Item da proposta não encontrado.")
    opportunity = _first("cti_oportunidades", opportunity_id, "Oportunidade da proposta não encontrada.")
    client = _first("clientes", client_id, "Cliente da proposta não encontrado.")
    return proposal, item, opportunity, client


def _document_metadata(proposal: dict[str, Any]) -> dict[str, Any]:
    metadata = proposal.get("arquivo_documento") or {}
    if not isinstance(metadata, dict) or not metadata.get("path") or not metadata.get("sha256"):
        raise HTTPException(status_code=409, detail="A proposta ainda não possui documento oficial finalizado.")
    return metadata


@router.post("/propostas/{proposal_id}/finalizar-documento")
def finalize_document(proposal_id: str):
    proposal, item, opportunity, client = _proposal_package(proposal_id)
    existing = proposal.get("arquivo_documento") or {}
    if isinstance(existing, dict) and existing.get("path"):
        return {"ok": True, "already_finalized": True, "document": existing, "proposal": proposal}

    snapshot = proposal.get("snapshot_dados") or {}
    application = snapshot.get("aplicacao") if isinstance(snapshot, dict) else {}
    try:
        result = finalize_official_proposal(
            supabase,
            proposta=proposal,
            item=item,
            oportunidade=opportunity,
            cliente=client,
            application=application if isinstance(application, dict) else {},
        )
    except ProposalDocumentRepositoryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"ok": True, "already_finalized": False, **result}


@router.post("/propostas/{proposal_id}/previsualizar-documento")
def preview_document(proposal_id: str, expires_in: int = 900):
    proposal, item, opportunity, client = _proposal_package(proposal_id)
    snapshot = proposal.get("snapshot_dados") or {}
    application = snapshot.get("aplicacao") if isinstance(snapshot, dict) else {}
    try:
        return preview_official_proposal(
            supabase,
            proposta=proposal,
            item=item,
            oportunidade=opportunity,
            cliente=client,
            application=application if isinstance(application, dict) else {},
            expires_in=expires_in,
        )
    except ProposalDocumentRepositoryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/propostas/{proposal_id}/documento-oficial")
def official_document(proposal_id: str, expires_in: int = 900):
    proposal = _first("cti_propostas", proposal_id, "Proposta não encontrada.")
    metadata = _document_metadata(proposal)
    validity = max(60, min(expires_in, 1800))
    try:
        response = supabase.storage.from_(FINAL_BUCKET).create_signed_url(str(metadata["path"]), validity)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível criar o acesso temporário ao documento oficial.") from exc
    if isinstance(response, dict):
        url = response.get("signedURL") or response.get("signed_url")
    else:
        url = getattr(response, "signed_url", None) or getattr(response, "signedURL", None)
    if not url:
        raise HTTPException(status_code=502, detail="O storage não retornou a URL temporária do documento oficial.")
    return {
        "proposal_id": proposal_id,
        "document": metadata,
        "url": str(url),
        "expires_in": validity,
    }
