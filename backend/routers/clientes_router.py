from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase_client import supabase

router = APIRouter()

# ------------------------------
# MODEL
# ------------------------------

class Cliente(BaseModel):
    nome: str
    cidade: str
    estado: str
    segmento: str


# ------------------------------
# CREATE CLIENTE
# ------------------------------

@router.post("/clientes")
def criar_cliente(cliente: Cliente):

    try:
        data = cliente.dict()

        response = supabase.table("clientes").insert(data).execute()

        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
