from routers.cti_api_router import router as cti_api_router
from routers.upload_router import router as upload_router


def _paths(router):
    return {getattr(route, "path", None) for route in router.routes}


def test_upload_anfir_canônico_permanece_explícito():
    assert "/upload/anfir/seguro" in _paths(upload_router)


def test_cti_api_não_reexpõe_alias_genérico_de_upload():
    assert "/upload" not in _paths(cti_api_router)
