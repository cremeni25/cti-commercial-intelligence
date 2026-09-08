from routers import crm_scope_mapa_insights_router as insights


def test_evolucao_mensal_e_total_fecham_antes_da_marca():
    base = [
        {"ano": 2026, "mes": 1, "linha": "TR", "quantidade": 2, "status": ""},
        {"ano": 2026, "mes": 2, "linha": "TR", "quantidade": 4, "status": "Carrier"},
        {"ano": 2026, "mes": 3, "linha": "TR", "quantidade": 6, "status": "TK"},
    ]
    trailer = next(item for item in insights._linhas_2026(base)["linhas"] if item["codigo"] == "trailer")
    assert trailer["mensal"][:3] == [2, 4, 6]
    assert trailer["total_2026"] == 12
