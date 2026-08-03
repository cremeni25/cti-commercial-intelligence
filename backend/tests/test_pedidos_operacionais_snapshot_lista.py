from routers.pedidos_operacionais_router import _equipamento_pedido


def test_equipamento_recupera_primeiro_item_da_lista_snapshot():
    pacote = {
        "item": None,
        "proposta": {"snapshot_dados": {"itens": [{"modelo_equipamento": "SUPRA 750"}]}},
        "pedido": {},
    }
    assert _equipamento_pedido(pacote) == "SUPRA 750"
