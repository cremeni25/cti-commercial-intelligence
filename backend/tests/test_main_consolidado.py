from main import app


def _paths():
    return {getattr(route, "path", None) for route in app.routes}


def test_main_nao_expoe_escritas_legadas():
    paths = _paths()
    assert "/processar" not in paths
    assert "/upload" not in paths


def test_rotas_operacionais_e_leituras_mantidas():
    paths = _paths()
    assert "/upload/anfir/seguro" in paths
    assert "/dashboard/insights" in paths
    assert "/debug/amostra" in paths
    assert "/pipeline/status" in paths
    assert "/status" in paths
