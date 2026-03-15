from fastapi import APIRouter
from pydantic import BaseModel
from core.supabase_client import supabase

router = APIRouter()

class Negociacao(BaseModel):

    cliente: str
    cidade: str | None = None
    estado: str | None = None
    produto: str | None = None
    valor: float | None = None
    status: str | None = None


@router.post("/negociacoes")
def criar_negociacao(negociacao: Negociacao):

    response = supabase.table("negociacoes").insert(
        negociacao.dict()
    ).execute()

    return response.data


@router.get("/negociacoes")
def listar_negociacoes():

    response = supabase.table("negociacoes").select("*").execute()

    return response.data
