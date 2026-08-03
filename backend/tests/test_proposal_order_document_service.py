from __future__ import annotations

import hashlib

import pytest

from services.proposal_order_document_service import (
    ProposalOrderDocumentError,
    load_official_document_attachment,
    upsert_official_document_in_dossier,
)


class _StorageBucket:
    def __init__(self, content: bytes):
        self.content = content

    def download(self, path: str) -> bytes:
        assert path == "propostas/p1/v1/proposta.docx"
        return self.content


class _Storage:
    def __init__(self, content: bytes):
        self.content = content

    def from_(self, bucket: str) -> _StorageBucket:
        assert bucket == "documentos-comerciais-cti"
        return _StorageBucket(self.content)


class _Supabase:
    def __init__(self, content: bytes):
        self.storage = _Storage(content)


def _proposal(content: bytes) -> dict:
    return {
        "arquivo_documento": {
            "bucket": "documentos-comerciais-cti",
            "path": "propostas/p1/v1/proposta.docx",
            "filename": "proposta.docx",
            "sha256": hashlib.sha256(content).hexdigest(),
            "template_code": "SUPRA_750",
            "template_version": 1,
            "source_sha256": "source-hash",
            "immutable": True,
        }
    }


def test_loads_exact_official_document_and_builds_resend_attachment():
    content = b"official-docx"
    attachment = load_official_document_attachment(_Supabase(content), _proposal(content))

    assert attachment.content == content
    assert attachment.filename == "proposta.docx"
    assert attachment.sha256 == hashlib.sha256(content).hexdigest()
    assert attachment.resend_payload()["filename"] == "proposta.docx"
    assert attachment.resend_payload()["content"]


def test_rejects_hash_divergence():
    proposal = _proposal(b"expected")
    with pytest.raises(ProposalOrderDocumentError, match="SHA-256"):
        load_official_document_attachment(_Supabase(b"changed"), proposal)


def test_dossier_keeps_only_one_official_document_reference():
    content = b"official-docx"
    attachment = load_official_document_attachment(_Supabase(content), _proposal(content))
    dossier = [
        {"tipo": "PROPOSTA", "id": "p1"},
        {"tipo": "DOCUMENTO_OFICIAL_PROPOSTA", "sha256": "old"},
    ]

    updated = upsert_official_document_in_dossier(dossier, attachment)
    official = [item for item in updated if item["tipo"] == "DOCUMENTO_OFICIAL_PROPOSTA"]

    assert len(official) == 1
    assert official[0]["sha256"] == attachment.sha256
    assert official[0]["immutable"] is True
