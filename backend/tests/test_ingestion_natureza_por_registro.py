from core.ingestion_reconciliation import avaliar_item, preparar_plano


def test_lote_comercial_classifica_cada_registro_por_natureza():
    plano = preparar_plano(
        "COMERCIAL",
        [
            {"indice": 1, "dados": {"cnpj": "11.111.111/0001-11", "razao_social": "Cliente A"}},
            {"indice": 2, "dados": {"id_oportunidade": "OP-1", "cliente": "Cliente A"}},
            {"indice": 3, "dados": {"numero_pedido": "PED-1", "id_oportunidade": "OP-1", "cliente": "Cliente A"}},
            {"indice": 4, "dados": {"numero_venda": "VEN-1", "numero_pedido": "PED-1", "id_oportunidade": "OP-1", "cliente": "Cliente A"}},
        ],
    )

    assert [item["entidade_sugerida"] for item in plano["itens"]] == [
        "CLIENTE",
        "OPORTUNIDADE",
        "PEDIDO",
        "VENDA",
    ]
    assert [item["natureza_canonica"] for item in plano["itens"]] == [
        "CRM_CADASTRAL",
        "FUNIL_COMERCIAL",
        "CRM_EXECUCAO_POS_OPORTUNIDADE",
        "COMERCIAL_REALIZADO",
    ]
    assert plano["lote_misto_naturezas"] is True
    assert plano["roteamento_por_registro"] is True
    assert plano["total_conflitos"] == 0


def test_venda_prevalece_quando_registro_preserva_referencias_do_ciclo_anterior():
    item = avaliar_item(
        "COMERCIAL",
        {
            "indice": 7,
            "dados": {
                "numero_venda": "VEN-7",
                "numero_pedido": "PED-7",
                "id_oportunidade": "OP-7",
                "cliente": "Cliente X",
            },
        },
    )

    assert item["entidade_sugerida"] == "VENDA"
    assert item["natureza_canonica"] == "COMERCIAL_REALIZADO"
    assert item["camada_dashboard"] == "REALIZADO_COMERCIAL"
    assert item["status_item"] == "VALIDO"


def test_registro_comercial_sem_natureza_identificavel_fica_em_conflito():
    item = avaliar_item(
        "COMERCIAL",
        {"indice": 9, "dados": {"observacao": "registro sem identificador comercial"}},
    )

    assert item["entidade_sugerida"] == "REGISTRO_COMERCIAL"
    assert item["natureza_canonica"] == "CRM_COMERCIAL_NAO_CLASSIFICADO"
    assert item["camada_dashboard"] == "STAGING_COMERCIAL"
    assert item["status_item"] == "CONFLITO"
    assert any(conflito["tipo"] == "NATUREZA_COMERCIAL_NAO_IDENTIFICADA" for conflito in item["conflitos"])
