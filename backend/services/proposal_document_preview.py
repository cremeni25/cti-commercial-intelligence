from __future__ import annotations

import hmac
from hashlib import sha256
from typing import Any, Mapping

from services.docx_pdf_conversion_service import DocxPdfConversionError, convert_docx_to_pdf
from services.official_proposal_document import render_official_docx, verify_media_preserved
from services.proposal_document_payload import build_proposal_document_payload
from services.proposal_template_catalog import template_for_equipment
from services.proposal_document_repository import MASTER_BUCKET, ProposalDocumentRepositoryError


def build_preview_official_proposal(
    supabase: Any,
    *,
    proposta: Mapping[str, Any],
    item: Mapping[str, Any],
    oportunidade: Mapping[str, Any],
    cliente: Mapping[str, Any],
    application: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    equipment = str(item.get("equipamento") or "").strip()
    template = template_for_equipment(equipment)
    rows = (
        supabase.table("cti_modelos_proposta")
        .select("*")
        .eq("equipamento", template.equipment)
        .eq("versao", template.version)
        .eq("ativo", True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise ProposalDocumentRepositoryError("Modelo oficial ativo não encontrado.")

    model = rows[0]
    source_path = str(model.get("arquivo_template_storage") or "").strip()
    expected_hash = str(model.get("arquivo_template_hash_sha256") or "").lower()
    if not source_path or not expected_hash:
        raise ProposalDocumentRepositoryError("Modelo oficial sem arquivo mestre ou SHA-256 registrado.")

    try:
        source = bytes(supabase.storage.from_(MASTER_BUCKET).download(source_path))
    except Exception as exc:
        raise ProposalDocumentRepositoryError(f"Falha ao baixar o arquivo mestre: {exc}") from exc
    if not source:
        raise ProposalDocumentRepositoryError("Arquivo mestre indisponível no bucket privado.")

    source_hash = sha256(source).hexdigest()
    if not hmac.compare_digest(source_hash.lower(), expected_hash):
        raise ProposalDocumentRepositoryError("SHA-256 do arquivo mestre diverge do registro técnico.")

    payload = build_proposal_document_payload(
        proposal=dict(proposta),
        item=dict(item),
        opportunity=dict(oportunidade),
        client=dict(cliente),
        validate_required=False,
    )

    output_number = str(proposta.get("numero") or proposta.get("id") or "PROPOSTA")
    preview_mode = "PREENCHIDA"
    try:
        generated = render_official_docx(
            source,
            equipment,
            payload,
            output_number=output_number,
            validate_required=False,
        )
        if not verify_media_preserved(source, generated.content):
            raise ProposalDocumentRepositoryError("Imagens, logomarca Carrier ou estrutura protegida foram alteradas.")
        docx_content = generated.content
        docx_filename = generated.filename
        docx_sha256 = generated.sha256
    except Exception as exc:
        if "âncoras contínuas seguras" not in str(exc):
            raise ProposalDocumentRepositoryError(f"Falha ao preencher o modelo oficial: {exc}") from exc
        docx_content = source
        docx_filename = f"{output_number}-{template.code}-v{template.version}-VALIDACAO.docx"
        docx_sha256 = source_hash
        preview_mode = "MESTRE_INTEGRO"

    try:
        pdf = convert_docx_to_pdf(docx_content, docx_filename)
    except DocxPdfConversionError as exc:
        raise ProposalDocumentRepositoryError(f"Não foi possível gerar o PDF para visualização: {exc}") from exc

    return {
        "content": pdf.content,
        "filename": pdf.filename,
        "sha256": pdf.sha256,
        "source_sha256": source_hash,
        "intermediate_docx_sha256": docx_sha256,
        "template_code": template.code,
        "template_version": template.version,
        "homologado": bool(model.get("homologado_em")),
        "preview_mode": preview_mode,
        "mime_type": "application/pdf",
    }
