from main import app
from routers.upload_router import router as upload_router


def _paths(router):
    return {getattr(route, "path", None) for route in router.routes}


def test_main_nao_expoe_escritas_legadas():
    paths = _paths(app)
    assert "/processar" not in paths
    assert "/upload" not in paths


def test_rotas_operacionais_e_leituras_mantidas():
    paths = _paths(app)
    assert "/dashboard/insights" in paths
    assert "/debug/amostra" in paths
    assert "/pipeline/status" in paths
    assert "/status" in paths
    assert "/upload/anfir/seguro" in _paths(upload_router)
