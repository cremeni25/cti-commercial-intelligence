from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Mapping

from services.proposal_document_repository import (
    FINAL_BUCKET,
    ProposalDocumentRepositoryError,
    finalize_official_proposal,
)


class ProposalOrderDocumentError(RuntimeError):
    pass


@dataclass(frozen=True)
class OfficialDocumentAttachment:
    filename: str
    content: bytes
    sha256: str
    bucket: str
    path: str
    template_code: str | None
    template_version: int | None
    source_sha256: str | None

    def resend_payload(self) -> dict[str, str]:
        return {
            "filename": self.filename,
            "content": base64.b64encode(self.content).decode("ascii"),
        }

    def dossier_record(self) -> dict[str, Any]:
        return {
            "tipo": "DOCUMENTO_OFICIAL_PROPOSTA",
            "bucket": self.bucket,
            "path": self.path,
            "filename": self.filename,
            "sha256": self.sha256,
            "template_code": self.template_code,
            "template_version": self.template_version,
            "source_sha256": self.source_sha256,
            "immutable": True,
        }


def _metadata_value(proposal: Mapping[str, Any]) -> Mapping[str, Any] | None:
    direct = proposal.get("arquivo_documento")
    if isinstance(direct, Mapping) and direct:
        return direct

    snapshot = proposal.get("snapshot_dados") or {}
    if isinstance(snapshot, Mapping):
        nested = snapshot.get("arquivo_documento")
        if isinstance(nested, Mapping) and nested:
            return nested
    return None


def _validate_metadata(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None:
        raise ProposalOrderDocumentError("A proposta ainda não possui documento oficial finalizado.")
    required = ("path", "filename", "sha256")
    missing = [field for field in required if not str(value.get(field) or "").strip()]
    if missing:
        raise ProposalOrderDocumentError(
            "O documento oficial está incompleto: " + ", ".join(missing)
        )
    if value.get("immutable") is not True:
        raise ProposalOrderDocumentError("O documento oficial da proposta não está marcado como imutável.")
    return value


def _first(supabase: Any, table: str, record_id: str) -> dict[str, Any] | None:
    if not record_id:
        return None
    try:
        rows = supabase.table(table).select("*").eq("id", record_id).limit(1).execute().data or []
    except Exception:
        return None
    return rows[0] if rows else None


def _finalize_if_missing(supabase: Any, proposal: Mapping[str, Any]) -> Mapping[str, Any]:
    existing = _metadata_value(proposal)
    if existing is not None:
        return existing

    item_id = str(proposal.get("item_oportunidade_id") or "").strip()
    opportunity_id = str(proposal.get("oportunidade_id") or "").strip()
    client_id = str(proposal.get("cliente_id") or "").strip()
    if not item_id or not opportunity_id or not client_id:
        raise ProposalOrderDocumentError(
            "A proposta não possui vínculos suficientes para finalizar o documento oficial."
        )

    item = _first(supabase, "cti_oportunidade_itens", item_id)
    opportunity = _first(supabase, "cti_oportunidades", opportunity_id)
    client = _first(supabase, "cti_clientes", client_id) or _first(supabase, "clientes", client_id)
    if not item or not opportunity or not client:
        raise ProposalOrderDocumentError(
            "Não foi possível recuperar os dados vinculados para finalizar o documento oficial."
        )

    snapshot = proposal.get("snapshot_dados") or {}
    application = snapshot.get("aplicacao") if isinstance(snapshot, Mapping) else {}
    try:
        finalized = finalize_official_proposal(
            supabase,
            proposta=proposal,
            item=item,
            oportunidade=opportunity,
            cliente=client,
            application=application if isinstance(application, Mapping) else {},
        )
    except (ProposalDocumentRepositoryError, ValueError) as exc:
        raise ProposalOrderDocumentError(str(exc)) from exc

    document = finalized.get("document") if isinstance(finalized, Mapping) else None
    if not isinstance(document, Mapping):
        raise ProposalOrderDocumentError("A finalização do documento oficial não retornou metadados válidos.")
    return document


def load_official_document_attachment(
    supabase: Any,
    proposal: Mapping[str, Any],
) -> OfficialDocumentAttachment:
    metadata = _validate_metadata(_finalize_if_missing(supabase, proposal))
    bucket = str(metadata.get("bucket") or FINAL_BUCKET)
    path = str(metadata["path"])
    try:
        content = supabase.storage.from_(bucket).download(path)
    except Exception as exc:
        raise ProposalOrderDocumentError(
            "Não foi possível recuperar o documento oficial para anexar ao pedido."
        ) from exc
    if not content:
        raise ProposalOrderDocumentError("O documento oficial armazenado está vazio.")

    raw = bytes(content)
    digest = hashlib.sha256(raw).hexdigest()
    expected = str(metadata["sha256"]).lower()
    if not hmac.compare_digest(digest.lower(), expected):
        raise ProposalOrderDocumentError(
            "O SHA-256 do documento oficial diverge do arquivo finalizado da proposta."
        )

    version = metadata.get("template_version")
    return OfficialDocumentAttachment(
        filename=str(metadata["filename"]),
        content=raw,
        sha256=digest,
        bucket=bucket,
        path=path,
        template_code=str(metadata.get("template_code") or "") or None,
        template_version=int(version) if version is not None else None,
        source_sha256=str(metadata.get("source_sha256") or "") or None,
    )


def upsert_official_document_in_dossier(
    dossier: list[dict[str, Any]],
    attachment: OfficialDocumentAttachment,
) -> list[dict[str, Any]]:
    updated = [
        item
        for item in dossier
        if not (
            isinstance(item, dict)
            and item.get("tipo") == "DOCUMENTO_OFICIAL_PROPOSTA"
        )
    ]
    updated.append(attachment.dossier_record())
    return updated
