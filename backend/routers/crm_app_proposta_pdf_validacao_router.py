from __future__ import annotations

import base64
from typing import Any

import fitz
from fastapi import APIRouter, HTTPException, Response

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


def _gerar_pdf_oficial(proposta_id: str):
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
        expected_pages = int(preview.get("expected_pages") or 4)
        pdf = convert_docx_to_pdf(
            bytes(preview["content"]),
            str(preview["filename"]),
            expected_pages=expected_pages,
        )
    except (ProposalDocumentRepositoryError, DocxPdfConversionError) as exc:
        raise HTTPException(status_code=503, detail=f"Não foi possível gerar o PDF oficial da proposta: {exc}") from exc
    return proposta, preview, pdf


def _renderizar_paginas(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Renderiza o PDF oficial em imagens para visualização estável em mobile/Android."""
    paginas: list[dict[str, Any]] = []
    try:
        documento = fitz.open(stream=pdf_bytes, filetype="pdf")
        matriz = fitz.Matrix(1.6, 1.6)
        for indice, pagina in enumerate(documento):
            pixmap = pagina.get_pixmap(matrix=matriz, alpha=False)
            png = pixmap.tobytes("png")
            paginas.append({
                "numero": indice + 1,
                "imagem": "data:image/png;base64," + base64.b64encode(png).decode("ascii"),
            })
        documento.close()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Não foi possível renderizar a proposta para visualização: {exc}") from exc
    return paginas


@router.get("/{proposta_id}/validar-pdf")
def validar_pdf_oficial(proposta_id: str):
    """Gera e valida o PDF oficial sem persistir documento e sem enviar e-mail."""
    proposta, preview, pdf = _gerar_pdf_oficial(proposta_id)
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


@router.get("/{proposta_id}/visualizar-pdf")
def visualizar_pdf_oficial(proposta_id: str):
    """Entrega o PDF oficial para clientes que suportam visualização PDF inline."""
    proposta, _preview, pdf = _gerar_pdf_oficial(proposta_id)
    numero = str(proposta.get("numero") or proposta_id).replace('"', "")
    return Response(
        content=pdf.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{numero}.pdf"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{proposta_id}/visualizar-paginas")
def visualizar_paginas_oficiais(proposta_id: str):
    """Entrega as páginas do documento oficial como imagens para o visualizador interno do APP CRM."""
    proposta, _preview, pdf = _gerar_pdf_oficial(proposta_id)
    return {
        "success": True,
        "somente_leitura": True,
        "proposta_id": proposta_id,
        "numero": str(proposta.get("numero") or proposta_id),
        "paginas": _renderizar_paginas(pdf.content),
        "email_enviado": False,
        "persistido": False,
    }
