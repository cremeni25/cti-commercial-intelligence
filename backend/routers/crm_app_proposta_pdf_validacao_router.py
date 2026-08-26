from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase
from routers.propostas_primeira_pagina_router import validar_documento_para_emissao
from services.docx_pdf_conversion_service import DocxPdfConversionError, convert_docx_to_pdf
from services.proposal_document_preview import build_preview_official_proposal
from services.proposal_document_repository import ProposalDocumentRepositoryError

router = APIRouter(prefix="/crm-app/propostas", tags=["CRM App - Validação PDF"])


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail=detalhe)
    return dados[0]


def _cliente(cliente_id: str) -> dict[str, Any]:
    for tabela in ("clientes", "cti_clientes"):
        try:
            dados = supabase.table(tabela).select("*").eq("id", cliente_id).limit(1).execute().data or []
        except Exception:
            dados = []
        if dados:
            return dados[0]
    return {}


@router.get("/{proposta_id}/validar-pdf")
def validar_pdf_oficial(proposta_id: str):
    """Gera e valida o PDF oficial sem persistir documento e sem enviar e-mail."""
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada.")
    item_id = str(proposta.get("item_oportunidade_id") or "")
    oportunidade_id = str(proposta.get("oportunidade_id") or "")
    cliente_id = str(proposta.get("cliente_id") or "")
    if not item_id or not oportunidade_id or not cliente_id:
        raise HTTPException(status_code=422, detail="A proposta não possui os vínculos comerciais necessários para gerar o documento.")

    item = _primeiro("cti_oportunidade_itens", item_id, "Item comercial da proposta não encontrado.")
    validar_documento_para_emissao(proposta, item)
    oportunidade = _primeiro("cti_oportunidades", oportunidade_id, "Oportunidade da proposta não encontrada.")
    cliente = _cliente(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente da proposta não encontrado.")

    try:
        preview = build_preview_official_proposal(
            supabase,
            proposta=proposta,
            item=item,
            oportunidade=oportunidade,
            cliente=cliente,
        )
        pdf = convert_docx_to_pdf(bytes(preview["content"]), str(preview["filename"]))
    except (ProposalDocumentRepositoryError, DocxPdfConversionError) as exc:
        raise HTTPException(status_code=503, detail=f"Não foi possível validar o PDF oficial da proposta: {exc}") from exc

    return {
        "success": True,
        "somente_leitura": True,
        "proposta_id": proposta_id,
        "numero": str(proposta.get("numero") or proposta_id),
        "fonte_docx": str(preview["filename"]),
        "arquivo_pdf": pdf.filename,
        "sha256": pdf.sha256,
        "paginas": pdf.page_count,
        "bytes": len(pdf.content),
        "email_enviado": False,
        "persistido": False,
    }
