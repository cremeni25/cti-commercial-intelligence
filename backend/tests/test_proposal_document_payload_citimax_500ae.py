from services.proposal_document_payload import build_proposal_document_payload


def test_citimax_500ae_usa_nome_comercial_no_tipo_de_equipamento():
    payload = build_proposal_document_payload(
        proposal={"numero": "PROP-TESTE"},
        item={
            "equipamento": "CITIMAX 500AE",
            "configuracao": "ACOPLADO_E_ELETRICO",
            "quantidade": 1,
            "preco_unitario": 41000,
        },
        opportunity={},
        client={"nome": "Cliente Teste"},
        validate_required=False,
    )

    assert payload.fields["equipment"] == "CITIMAX 500AE"
    assert payload.fields["configuration"] == "CITIMAX 500AE"
