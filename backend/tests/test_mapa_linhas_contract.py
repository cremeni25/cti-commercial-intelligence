from routers import crm_scope_mapa_insights_router as insights


def test_linha_primeiro_e_marca_depois_no_mesmo_denominador():
    base = [
        {"ano": 2026, "mes": 1, "linha": "TR", "quantidade": 4, "status": "Carrier", "fabricante_equipamento": "Carrier"},
        {"ano": 2026, "mes": 1, "linha": "TR", "quantidade": 3, "status": "TK", "fabricante_equipamento": "Thermo King"},
        {"ano": 2026, "mes": 2, "linha": "TR", "quantidade": 2, "status": "Nacional", "fabricante_equipamento": ""},
        {"ano": 2026, "mes": 2, "linha": "TR", "quantidade": 1, "status": "", "fabricante_equipamento": ""},
    ]
    trailer = next(item for item in insights._linhas_2026(base)["linhas"] if item["codigo"] == "trailer")
    assert trailer["total_2026"] == 10
    assert trailer["mensal"][:2] == [7, 3]
    assert sum(trailer["mensal"]) == trailer["total_2026"]
    assert trailer["composicao_marca"]["mercado"] == trailer["total_2026"]
    assert trailer["composicao_marca"]["fechamento_ok"] is True
    assert trailer["composicao_marca"]["fechamento_total"] == trailer["total_2026"]
