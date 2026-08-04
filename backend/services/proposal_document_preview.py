from __future__ import annotations

import hmac
from typing import Any, Mapping

from services.official_proposal_document import render_official_docx, verify_media_preserved
from services.proposal_document_payload import build_proposal_document_payload
from services.proposal_template_catalog import template_for_equipment
from services.proposal_document_repository import FINAL_BUCKET, MASTER_BUCKET, ProposalDocumentRepositoryError


def preview_official_proposal(
    supabase: Any,
    *,
    proposta: Mapping[str, Any],
    item: Mapping[str, Any],
    oportunidade: Mapping[str, Any],
    cliente: Mapping[str, Any],
    application: Mapping[str, Any] | None = None,
    expires_in: int = 900,
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
        source = supabase.storage.from_(MASTER_BUCKET).download(source_path)
    except Exception as exc:
        raise ProposalDocumentRepositoryError(f"Falha ao recuperar o arquivo mestre: {exc}") from exc
    if not source:
        raise ProposalDocumentRepositoryError("Arquivo mestre indisponível no bucket privado.")

    payload = build_proposal_document_payload(
        proposta=proposta,
        item=item,
        oportunidade=oportunidade,
        cliente=cliente,
        application=application or {},
    )
    generated = render_official_docx(
        bytes(source),
        equipment,
        payload,
        output_number=str(proposta.get("numero") or proposta.get("id") or "PROPOSTA"),
    )
    if not hmac.compare_digest(generated.source_sha256.lower(), expected_hash):
        raise ProposalDocumentRepositoryError("SHA-256 do arquivo mestre diverge do registro técnico.")
    if not verify_media_preserved(bytes(source), generated.content):
        raise ProposalDocumentRepositoryError("Imagens, logomarca Carrier ou estrutura protegida foram alteradas.")

    proposal_id = str(proposta.get("id") or "").strip()
    version = int(proposta.get("versao") or 1)
    path = f"previews/propostas/{proposal_id}/v{version}/{generated.filename}"
    bucket = supabase.storage.from_(FINAL_BUCKET)

    try:
        bucket.remove([path])
    except Exception:
        pass

    try:
        uploaded = bucket.upload(
            path,
            generated.content,
            {
                "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "upsert": "false",
            },
        )
    except Exception as exc:
        raise ProposalDocumentRepositoryError(f"Falha ao armazenar a pré-visualização oficial: {exc}") from exc
    if not uploaded:
        raise ProposalDocumentRepositoryError("O storage não confirmou a pré-visualização oficial.")

    validity = max(60, min(expires_in, 1800))
    try:
        signed = bucket.create_signed_url(path, validity)
    except Exception as exc:
        raise ProposalDocumentRepositoryError(f"Falha ao criar acesso temporário à pré-visualização: {exc}") from exc
    if isinstance(signed, dict):
        url = signed.get("signedURL") or signed.get("signed_url")
    else:
        url = getattr(signed, "signed_url", None) or getattr(signed, "signedURL", None)
    if not url:
        raise ProposalDocumentRepositoryError("O storage não retornou acesso temporário à pré-visualização.")

    return {
        "proposal_id": proposal_id,
        "preview": True,
        "homologado": bool(model.get("homologado_em")),
        "document": {
            "filename": generated.filename,
            "sha256": generated.sha256,
            "source_sha256": generated.source_sha256,
            "template_code": generated.template_code,
            "template_version": generated.template_version,
            "preserves_images": True,
            "preserves_carrier_branding": True,
            "immutable": False,
        },
        "url": str(url),
        "expires_in": validity,
    }
