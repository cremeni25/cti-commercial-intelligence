from routers import drilldown_router as mod


def test_filtro_historico_individualiza_total(monkeypatch):
    rows = (
        {"ano": 2024, "status": "PERDIDO", "cliente": "A", "equipamento": "X4 7500", "data": "2024-01-10"},
        {"ano": 2024, "status": "GANHO", "cliente": "B", "equipamento": "X4 7500", "data": "2024-02-10"},
        {"ano": 2025, "status": "PERDIDO", "cliente": "C", "equipamento": "SUPRA 850", "data": "2025-01-10"},
    )
    monkeypatch.setattr(mod, "carregar_historico_comercial", lambda: rows)
    resposta = mod.detalhamento_indicador(camada="historico", campo="ano", valor="2024", periodo="TODO_HISTORICO")
    assert resposta["total_registros"] == 2
    assert {item["cliente"] for item in resposta["registros"]} == {"A", "B"}


def test_busca_respeita_recorte_historico(monkeypatch):
    rows = (
        {"status": "PERDIDO", "cliente": "CLIENTE ALFA", "equipamento": "X4 7500", "data": "2024-01-10"},
        {"status": "PERDIDO", "cliente": "CLIENTE BETA", "equipamento": "SUPRA 850", "data": "2024-02-10"},
        {"status": "GANHO", "cliente": "CLIENTE ALFA", "equipamento": "SUPRA 850", "data": "2024-03-10"},
    )
    monkeypatch.setattr(mod, "carregar_historico_comercial", lambda: rows)
    resposta = mod.detalhamento_indicador(camada="historico", campo="status", valor="PERDIDO", busca="ALFA", periodo="TODO_HISTORICO")
    assert resposta["total_registros"] == 1
    assert resposta["registros"][0]["cliente"] == "CLIENTE ALFA"


def test_paginacao_preserva_total(monkeypatch):
    rows = tuple({"status": "PERDIDO", "cliente": f"CLIENTE {i}", "data": "2024-01-10"} for i in range(65))
    monkeypatch.setattr(mod, "carregar_historico_comercial", lambda: rows)
    resposta = mod.detalhamento_indicador(camada="historico", campo="status", valor="PERDIDO", pagina=2, limite=50, periodo="TODO_HISTORICO")
    assert resposta["total_registros"] == 65
    assert resposta["total_paginas"] == 2
    assert len(resposta["registros"]) == 15


def test_campos_invalidos_sao_rejeitados():
    try:
        mod.detalhamento_indicador(camada="historico", campo="campo_inexistente", valor="X")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("Campo arbitrário não deveria ser aceito no drill-down")
