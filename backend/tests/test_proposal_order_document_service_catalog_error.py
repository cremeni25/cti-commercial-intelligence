from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services.proposal_order_document_service import ProposalOrderDocumentError, load_official_document_attachment


class Query:
    def __init__(self, rows):
        self.rows = rows
    def select(self, *_): return self
    def eq(self, *_): return self
    def limit(self, *_): return self
    def execute(self): return SimpleNamespace(data=self.rows)


class Supabase:
    def table(self, name):
        rows = {
            "cti_oportunidade_itens": [{"id": "item-1", "equipamento": "MODELO INEXISTENTE"}],
            "cti_oportunidades": [{"id": "opp-1"}],
            "cti_clientes": [{"id": "cli-1"}],
        }
        return Query(rows.get(name, []))


@patch("services.proposal_order_document_service.finalize_official_proposal", side_effect=ValueError("Equipamento sem modelo oficial"))
def test_catalog_resolution_error_becomes_functional_order_error(_finalize):
    proposal = {
        "id": "p1",
        "item_oportunidade_id": "item-1",
        "oportunidade_id": "opp-1",
        "cliente_id": "cli-1",
        "snapshot_dados": {},
    }
    with pytest.raises(ProposalOrderDocumentError, match="sem modelo oficial"):
        load_official_document_attachment(Supabase(), proposal)
