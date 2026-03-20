from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase_client import supabase

router = APIRouter()

# ------------------------------
# MODEL CORRETO (ALINHADO AO BANCO)
# ------------------------------

class Venda(BaseModel):
    cliente_id: str
    equipamento_id: str
    implementador_id: str
    tipo_venda: str
    valor: float
    data_venda: str
    observacao: str | None = None


# ------------------------------
# CREATE VENDA
# ------------------------------

@router.post("/vendas")
def criar_venda(venda: Venda):

    try:
        data = venda.dict()

        response = supabase.table("vendas").insert(data).execute()

        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
