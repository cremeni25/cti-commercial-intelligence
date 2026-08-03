from __future__ import annotations

import hmac
from datetime import datetime, timezone
from typing import Any, Mapping

from services.official_proposal_document import render_official_docx, verify_media_preserved
from services.proposal_document_payload import build_proposal_document_payload
from services.proposal_template_catalog import template_for_equipment

MASTER_BUCKET = "modelos-propostas-carrier"
FINAL_BUCKET = "documentos-comerciais-cti"


class ProposalDocumentRepositoryError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finalize_official_proposal(
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
    if not model.get("homologado_em"):
        raise ProposalDocumentRepositoryError("Modelo oficial ainda não homologado visualmente.")

    source_path = str(model.get("arquivo_template_storage") or "").strip()
    expected_hash = str(model.get("arquivo_template_hash_sha256") or "").lower()
    if not source_path or not expected_hash:
        raise ProposalDocumentRepositoryError("Modelo oficial sem arquivo mestre ou SHA-256 registrado.")

    source = supabase.storage.from_(MASTER_BUCKET).download(source_path)
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
        raise ProposalDocumentRepositoryError("SHA-256 do arquivo mestre diverge do modelo homologado.")
    if not verify_media_preserved(bytes(source), generated.content):
        raise ProposalDocumentRepositoryError("Imagens, logomarca Carrier ou estrutura protegida foram alteradas.")

    proposal_id = str(proposta.get("id") or "").strip()
    if not proposal_id:
        raise ProposalDocumentRepositoryError("Proposta sem identificador persistente.")
    version = int(proposta.get("versao") or 1)
    path = f"propostas/{proposal_id}/v{version}/{generated.filename}"
    uploaded = supabase.storage.from_(FINAL_BUCKET).upload(
        path,
        generated.content,
        {
            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "upsert": "false",
        },
    )
    if not uploaded:
        raise ProposalDocumentRepositoryError("O storage não confirmou o documento final imutável.")

    metadata = {
        "bucket": FINAL_BUCKET,
        "path": path,
        "filename": generated.filename,
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "sha256": generated.sha256,
        "source_bucket": MASTER_BUCKET,
        "source_path": source_path,
        "source_sha256": generated.source_sha256,
        "template_code": generated.template_code,
        "template_version": generated.template_version,
        "finalized_at": _now(),
        "preserves_images": True,
        "preserves_carrier_branding": True,
        "immutable": True,
    }
    updated = (
        supabase.table("cti_propostas")
        .update({
            "arquivo_documento": metadata,
            "hash_documento": generated.sha256,
            "modelo_proposta_id": model.get("id"),
            "updated_at": metadata["finalized_at"],
        })
        .eq("id", proposal_id)
        .execute()
        .data
        or []
    )
    if not updated:
        raise ProposalDocumentRepositoryError("O vínculo do arquivo final com a proposta não foi confirmado.")
    return {"document": metadata, "proposal": updated[0]}
