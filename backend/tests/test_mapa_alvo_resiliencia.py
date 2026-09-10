from routers import ia_comercial_alvo_mapa_router as alvo_router


def test_localizar_alvo_tolera_variacao_textual_do_responsavel_quando_unico():
    direcionamento = {
        "alvos": [
            {
                "cliente": "CLIENTE TESTE LTDA",
                "responsavel": "Mônica Almeida",
                "unidades": 3,
            }
        ]
    }

    alvo = alvo_router._localizar_alvo(
        direcionamento,
        "cliente teste ltda",
        "MONICA ALMEIDA - VIENA",
    )

    assert alvo is direcionamento["alvos"][0]


def test_localizar_alvo_nao_assume_responsavel_quando_cliente_tem_mais_de_um():
    direcionamento = {
        "alvos": [
            {"cliente": "CLIENTE TESTE LTDA", "responsavel": "Responsável A"},
            {"cliente": "CLIENTE TESTE LTDA", "responsavel": "Responsável B"},
        ]
    }

    alvo = alvo_router._localizar_alvo(
        direcionamento,
        "CLIENTE TESTE LTDA",
        "Responsável inexistente",
    )

    assert alvo is None
