from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Mapping

from services.proposal_document_repository import FINAL_BUCKET


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


def _metadata(proposal: Mapping[str, Any]) -> Mapping[str, Any]:
    value = proposal.get("arquivo_documento") or {}
    if not isinstance(value, Mapping):
        raise ProposalOrderDocumentError("A proposta não possui metadados válidos do documento oficial.")
    required = ("path", "filename", "sha256")
    missing = [field for field in required if not str(value.get(field) or "").strip()]
    if missing:
        raise ProposalOrderDocumentError(
            "O documento oficial está incompleto: " + ", ".join(missing)
        )
    if value.get("immutable") is not True:
        raise ProposalOrderDocumentError("O documento oficial da proposta não está marcado como imutável.")
    return value


def load_official_document_attachment(
    supabase: Any,
    proposal: Mapping[str, Any],
) -> OfficialDocumentAttachment:
    metadata = _metadata(proposal)
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
