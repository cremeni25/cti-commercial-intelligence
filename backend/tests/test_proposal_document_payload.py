import pytest

from services.proposal_document_payload import (
    ProposalDocumentDataError,
    build_proposal_document_payload,
)


def complete_payload():
    proposal = {"numero": "PROP-20260803-TESTE", "versao": 2, "validade": "31/08/2026"}
    item = {
        "equipamento": "SUPRA 750",
        "quantidade": 2,
        "preco_unitario": 105000,
        "desconto_percentual": 5,
        "condicao_pagamento": "30% de entrada e saldo em 3 parcelas",
        "frete": "CIF",
        "local_entrega": "Autorizada Carrier",
        "opcionais": ["Lynx Fleet", "Kit instalação"],
        "lynx_incluido": True,
        "lynx_meses": 12,
    }
    opportunity = {
        "cliente_nome": "Alto Padrão",
        "responsavel_id": "responsavel-1",
        "bau_largura_m": 2.4,
        "bau_comprimento_m": 6.0,
        "bau_altura_m": 2.5,
        "temperatura_transporte_c": -18,
    }
    client = {
        "razao_social": "Alto Padrão Transportes Ltda",
        "cnpj": "12.345.678/0001-90",
        "inscricao_estadual": "123.456.789.000",
        "endereco_completo": "Rua Exemplo, 100 - São Paulo/SP",
        "telefone": "(11) 99999-9999",
        "email": "compras@altopadrao.example",
    }
    return proposal, item, opportunity, client


def test_builds_official_template_payload_with_crm_data():
    proposal, item, opportunity, client = complete_payload()
    result = build_proposal_document_payload(
        proposal=proposal,
        item=item,
        opportunity=opportunity,
        client=client,
    )

    assert result.template_code == "SUPRA_750"
    assert result.template_filename == "SUPRA 750.docx"
    assert result.fields["client_name"] == "Alto Padrão Transportes Ltda"
    assert result.fields["client_tax_id"] == "12.345.678/0001-90"
    assert result.fields["body_length_m"] == 6.0
    assert result.fields["lynx_included"] is True
    assert result.fields["total_price"] == 199500.0


def test_rejects_generation_when_required_document_data_is_missing():
    proposal, item, opportunity, client = complete_payload()
    client["cnpj"] = None

    with pytest.raises(ProposalDocumentDataError, match="client_tax_id"):
        build_proposal_document_payload(
            proposal=proposal,
            item=item,
            opportunity=opportunity,
            client=client,
        )


def test_rejects_equipment_without_official_template():
    proposal, item, opportunity, client = complete_payload()
    item["equipamento"] = "MODELO NÃO CADASTRADO"

    with pytest.raises(ValueError, match="sem modelo oficial"):
        build_proposal_document_payload(
            proposal=proposal,
            item=item,
            opportunity=opportunity,
            client=client,
        )
