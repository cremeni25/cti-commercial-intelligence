from fastapi import HTTPException

from routers import propostas_documentos_oficiais_router as module


def test_document_metadata_requires_finalized_document():
    try:
        module._document_metadata({"arquivo_documento": {}})
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "ainda não possui" in str(exc.detail)
    else:
        raise AssertionError("Documento não finalizado deveria ser rejeitado")


def test_document_metadata_accepts_immutable_reference():
    metadata = {"path": "propostas/1/v1/doc.docx", "sha256": "abc", "immutable": True}
    assert module._document_metadata({"arquivo_documento": metadata}) == metadata


def test_official_routes_are_registered():
    paths = {route.path for route in module.router.routes}
    assert "/crm-documentos/propostas/{proposal_id}/finalizar-documento" in paths
    assert "/crm-documentos/propostas/{proposal_id}/documento-oficial" in paths
