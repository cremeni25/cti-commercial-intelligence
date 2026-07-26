from fastapi import APIRouter, UploadFile, File
from routers.upload_router import upload_anfir_seguro
from routers.product_catalog_router import router as product_catalog_router

router = APIRouter()
router.include_router(product_catalog_router)


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await upload_anfir_seguro(file)
