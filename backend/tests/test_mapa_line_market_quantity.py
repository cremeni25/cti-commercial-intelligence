from routers import crm_scope_mapa_insights_router as insights


def test_total_anual_e_mensal_usam_quantidade_da_anfir():
    resultado = insights._linhas_2026([
        {"ano": 2026, "mes": 1, "linha": "TR", "quantidade": 5, "status": "Carrier"},
        {"ano": 2026, "mes": 2, "linha": "TR", "quantidade": 7, "status": "TK"},
    ])
    trailer = next(item for item in resultado["linhas"] if item["codigo"] == "trailer")
    assert trailer["total_2026"] == 12
    assert trailer["mensal"][0] == 5
    assert trailer["mensal"][1] == 7
