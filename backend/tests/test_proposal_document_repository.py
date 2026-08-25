from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services.official_proposal_document import GeneratedOfficialDocument
from services.proposal_document_repository import ProposalDocumentRepositoryError, finalize_official_proposal


class Query:
    def __init__(self, rows):
        self.rows = rows
    def select(self, *_): return self
    def eq(self, *_): return self
    def limit(self, *_): return self
    def update(self, *_): return self
    def execute(self): return SimpleNamespace(data=self.rows)


class Bucket:
    def __init__(self, source=b"source"):
        self.source = source
        self.uploads = []
    def download(self, _): return self.source
    def upload(self, path, content, options):
        self.uploads.append((path, content, options))
        return {"path": path}


class Storage:
    def __init__(self):
        self.master = Bucket()
        self.final = Bucket()
    def from_(self, name):
        return self.master if name == "modelos-propostas-carrier" else self.final


class Supabase:
    def __init__(self, model):
        self.storage = Storage()
        self.model = model
    def table(self, name):
        if name == "cti_modelos_proposta": return Query([self.model])
        if name == "cti_propostas": return Query([{"id": "p1"}])
        raise AssertionError(name)


BASE_MODEL = {
    "id": "m1",
    "equipamento": "SUPRA 750",
    "versao": 1,
    "ativo": True,
    "homologado_em": "2026-08-03T00:00:00Z",
    "arquivo_template_storage": "diesel/supra-750/v1/SUPRA 750.docx",
    "arquivo_template_hash_sha256": "source-hash",
}


@patch("services.proposal_document_repository.build_proposal_document_payload", return_value={})
@patch("services.proposal_document_repository.verify_media_preserved", return_value=True)
@patch("services.proposal_document_repository.render_official_docx")
def test_final_document_is_uploaded_without_upsert_and_linked_to_proposal(render, _verify, payload):
    render.return_value = GeneratedOfficialDocument(
        filename="PROP-1-SUPRA_750-v1.docx",
        content=b"final",
        sha256="final-hash",
        template_code="SUPRA_750",
        template_version=1,
        source_sha256="source-hash",
    )
    supabase = Supabase(BASE_MODEL)
    result = finalize_official_proposal(
        supabase,
        proposta={"id": "p1", "numero": "PROP-1", "versao": 1},
        item={"equipamento": "SUPRA 750"},
        oportunidade={},
        cliente={},
    )
    path, content, options = supabase.storage.final.uploads[0]
    assert path == "propostas/p1/v1/fonte-source-hash/PROP-1-SUPRA_750-v1.docx"
    assert content == b"final"
    assert options["upsert"] == "false"
    assert result["document"]["immutable"] is True
    assert result["document"]["preserves_images"] is True
    assert result["document"]["preserves_carrier_branding"] is True
    assert payload.call_args.kwargs["validate_required"] is False
    assert render.call_args.kwargs["validate_required"] is False
    assert render.call_args.kwargs["require_all_requested_anchors"] is False


def test_non_homologated_model_is_rejected():
    model = {**BASE_MODEL, "homologado_em": None}
    with pytest.raises(ProposalDocumentRepositoryError, match="não homologado"):
        finalize_official_proposal(
            Supabase(model),
            proposta={"id": "p1"},
            item={"equipamento": "SUPRA 750"},
            oportunidade={},
            cliente={},
        )
