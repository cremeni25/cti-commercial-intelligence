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
    assert geral["metadata"]["natureza_dados"] == "FATO_MERCADO_REALIZADO"
    assert geral["metadata"]["contrato_dashboard"]["dashboard"] == "INTELIGENCIA_MERCADO"
    assert geral["kpis"]["conversao"] is None
    assert "conversao" not in geral["kpis"]["comparacoes"]
    assert geral["metricas_funil"]["disponiveis"] is False
    assert geral["oportunidades_perdidas"]["disponivel"] is False
    assert trailer["resumo"]["total_registros"] == 1
    assert trailer["implementadoras"][0]["nome"] == "RANDON"


def test_anfir_nao_inventa_perda_ou_conversao_de_funil():
    resultado = consolidar_inteligencia([
        {
            "cliente": "CLIENTE A",
            "produto": "TRAILER",
            "status": "PERDIDO",
            "motivo_perda": "PRECO",
            "data_venda": "2026-01-10",
        }
    ])

    assert resultado["kpis"]["conversao"] is None
    assert resultado["oportunidades_perdidas"]["quantidade"] is None
    assert resultado["serie_temporal"][0]["perdas"] is None


def test_empty_state_explicativo():
    resultado = consolidar_inteligencia([], "viena-sp", "DT")

    assert resultado["resumo"]["total_registros"] == 0
    assert resultado["empty_state"]
