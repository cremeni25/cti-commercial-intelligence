from fastapi import APIRouter, UploadFile, File
from routers.upload_router import upload_anfir_seguro
from routers.product_catalog_router import router as product_catalog_router
from routers.auth_router import router as auth_router
from routers.access_diagnostics_router import router as access_diagnostics_router

router = APIRouter()
router.include_router(product_catalog_router)
router.include_router(auth_router)
router.include_router(access_diagnostics_router)


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await upload_anfir_seguro(file)
