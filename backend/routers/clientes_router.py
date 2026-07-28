from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase_client import supabase

from routers.clientes_oportunidade_router import router as cliente_oportunidade_router

router = APIRouter()
router.include_router(cliente_oportunidade_router)


class Cliente(BaseModel):
    nome: str
    cidade: str
    estado: str
    segmento: str


@router.post("/clientes")
def criar_cliente(cliente: Cliente):
    try:
        data = cliente.model_dump()
        response = supabase.table("clientes").insert(data).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao criar cliente: {e}") from e
