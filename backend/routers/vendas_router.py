from fastapi import APIRouter
from pydantic import BaseModel
from core.supabase_client import supabase

router = APIRouter()

class Venda(BaseModel):

    cliente_id: str
    equipamento_id: str
    implementador_id: str
    valor: float
    data_venda: str


@router.get("/vendas")
def listar_vendas():

    vendas = supabase.table("vendas").select("*").execute()

    return vendas.data


@router.post("/vendas")
def criar_venda(venda: Venda):

    response = supabase.table("vendas").insert(venda.dict()).execute()

    return response.data
