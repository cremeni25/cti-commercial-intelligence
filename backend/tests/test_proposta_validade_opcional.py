from routers.propostas_primeira_pagina_router import campos_pendentes_documento


def test_validade_em_branco_nao_bloqueia_emissao(monkeypatch):
    monkeypatch.setattr(
        "routers.propostas_primeira_pagina_router.campos_documentais",
        lambda proposta, item: {
            "voltagem": "24",
            "tipo_equipamento": "PADRAO",
            "impostos": "04% ICMS/PIS/COFINS",
            "acessorios": None,
            "condicao_pagamento": "A combinar",
            "possui_entrada": False,
            "valor_entrada": None,
            "local_entrega": "AUTORIZADA CARRIER",
            "autorizada_nome_endereco": "EDS Guarulhos",
            "frete": "CIF",
            "prazo_entrega": "Imediato",
            "validade": None,
            "lynx_meses": None,
        },
    )
    monkeypatch.setattr(
        "routers.propostas_primeira_pagina_router._campo_existe_no_documento",
        lambda item, nome: nome == "voltagem",
    )

    assert campos_pendentes_documento({}, {"equipamento": "XARIOS 6"}) == []
