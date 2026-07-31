from fastapi import APIRouter, UploadFile, File
from routers.upload_router import upload_anfir_seguro
from routers.product_catalog_router import router as product_catalog_router
from routers.auth_router import router as auth_router
from routers.access_diagnostics_router import router as access_diagnostics_router
from routers.governanca_usuarios_router import router as governanca_usuarios_router
from routers.crm_visao_router import router as crm_visao_router
from routers.propostas_pedidos_router import router as propostas_pedidos_router
from routers.propostas_consulta_router import router as propostas_consulta_router
from routers.carrier_operacional_router import router as carrier_operacional_router
from routers.catalogo_comercial_router import router as catalogo_comercial_router

router = APIRouter()
router.include_router(product_catalog_router)
router.include_router(auth_router)
router.include_router(access_diagnostics_router)
router.include_router(governanca_usuarios_router)
router.include_router(crm_visao_router)
router.include_router(propostas_pedidos_router)
router.include_router(propostas_consulta_router)
router.include_router(carrier_operacional_router)
router.include_router(catalogo_comercial_router)


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await upload_anfir_seguro(file)
