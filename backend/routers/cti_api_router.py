from fastapi import APIRouter, UploadFile, File
from routers.upload_router import upload_anfir_seguro

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await upload_anfir_seguro(file)