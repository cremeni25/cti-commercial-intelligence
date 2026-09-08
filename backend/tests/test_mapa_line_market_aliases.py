from routers import crm_scope_mapa_insights_router as insights


def test_aliases_tr_dt_dd_sao_as_tres_familias_do_mapa():
    base = [
        {"ano": 2026, "mes": 1, "linha": "TR", "quantidade": 2},
        {"ano": 2026, "mes": 1, "linha": "DT", "quantidade": 3},
        {"ano": 2026, "mes": 1, "linha": "DD", "quantidade": 4},
    ]
    linhas = {item["codigo"]: item["total_2026"] for item in insights._linhas_2026(base)["linhas"]}
    assert linhas == {"trailer": 2, "diesel_truck": 3, "direct_drive": 4}
