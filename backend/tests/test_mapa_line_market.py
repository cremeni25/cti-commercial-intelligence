from services.mapa_line_market import composicao_marca_linha


def test_total_da_linha_independe_da_marca_e_fecha_100_porcento():
    registros = [
        {"quantidade": 2, "status": "Carrier", "fabricante_equipamento": "Carrier"},
        {"quantidade": 3, "status": "TK", "fabricante_equipamento": "Thermo King"},
        {"quantidade": 4, "status": "Nacional", "fabricante_equipamento": ""},
        {"quantidade": 1, "status": "", "fabricante_equipamento": ""},
    ]
    resultado = composicao_marca_linha(registros)
    assert resultado["mercado"] == 10
    assert resultado["carrier"] == 2
    assert resultado["outras_marcas"] == 7
    assert resultado["marca_nao_discriminada"] == 1
    assert resultado["fechamento_total"] == 10
    assert resultado["fechamento_ok"] is True
    assert resultado["carrier_pct"] == 20.0
    assert resultado["outras_marcas_pct"] == 70.0
    assert resultado["marca_nao_discriminada_pct"] == 10.0


def test_marca_nao_e_inventada_quando_arquivo_nao_discrimina():
    resultado = composicao_marca_linha([
        {"quantidade": 5, "status": "Nacional", "fabricante_equipamento": ""},
    ])
    assert resultado["mercado"] == 5
    assert resultado["outras_marcas"] == 5
    assert resultado["marcas_concorrentes"] == [
        {"nome": "OUTRA MARCA — NÃO DISCRIMINADA", "quantidade": 5, "percentual_mercado": 100.0}
    ]
