from fastapi import APIRouter
from pydantic import BaseModel
from core.supabase_client import supabase

router = APIRouter()

class Cliente(BaseModel):

    nome: str
    cidade: str
    estado: str
    segmento: str | None = None
    cnpj: str | None = None


@router.post("/clientes")
def criar_cliente(cliente: Cliente):

    result = supabase.table("clientes").insert(cliente.dict()).execute()

    return result.data


@router.get("/clientes")
def listar_clientes():

    result = supabase.table("clientes").select("*").execute()

    return result.data
