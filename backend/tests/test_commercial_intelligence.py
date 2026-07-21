from services.commercial_intelligence import consolidar_inteligencia


def test_consolida_inteligencia_por_segmento_e_taxonomia():
    registros = [
        {
            "produto": "TRAILER",
            "implementadora": "RANDON IMPLEMENTOS",
            "estado": "SP",
            "cliente": "CLIENTE A",
            "fabricante_equipamento": "CARRIER",
            "valor": 100,
            "data_venda": "2026-01-10",
        },
        {
            "produto": "DIRECT DRIVE",
            "implementadora": "FACCHINI",
            "estado": "RJ",
            "cliente": "CLIENTE B",
            "fabricante_equipamento": "THERMO KING",
            "valor": 200,
            "data_venda": "2026-02-10",
        },
    ]

    geral = consolidar_inteligencia(registros, "brasil", "GERAL")
    trailer = consolidar_inteligencia(registros, "brasil", "TR")

    assert geral["resumo"]["total_registros"] == 2
    assert geral["segmentos"] == {"TR": 1, "DT": 0, "DD": 1, "UNKNOWN": 0}
    assert geral["metadata"]["origem"] == "cti_anfir"
    assert trailer["resumo"]["total_registros"] == 1
    assert trailer["implementadoras"][0]["nome"] == "RANDON"


def test_empty_state_explicativo():
    resultado = consolidar_inteligencia([], "viena-sp", "DT")

    assert resultado["resumo"]["total_registros"] == 0
    assert resultado["empty_state"]
