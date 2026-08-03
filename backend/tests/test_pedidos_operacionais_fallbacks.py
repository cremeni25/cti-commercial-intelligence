from routers.pedidos_operacionais_router import _equipamento_pedido


def test_equipamento_prioriza_item():
    pacote = {"item": {"equipamento": "SUPRA 750"}, "proposta": {}, "pedido": {}}
    assert _equipamento_pedido(pacote) == "SUPRA 750"


def test_equipamento_recupera_snapshot():
    pacote = {
        "item": None,
        "proposta": {"snapshot_dados": {"item": {"equipamento": "SUPRA 750"}}},
        "pedido": {},
    }
    assert _equipamento_pedido(pacote) == "SUPRA 750"
