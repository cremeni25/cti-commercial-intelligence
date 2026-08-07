from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase_client import supabase

router = APIRouter()


class Venda(BaseModel):
    cliente_id: str
    equipamento_id: str
    implementador_id: str
    tipo_venda: str
    valor: float
    data_venda: str
    observacao: str | None = None


@router.get("/vendas")
def listar_vendas():
    try:
        response = (
            supabase.table("vendas")
            .select("*")
            .order("data_venda", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vendas")
def criar_venda(venda: Venda):
    try:
        data = venda.model_dump()
        response = supabase.table("vendas").insert(data).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
