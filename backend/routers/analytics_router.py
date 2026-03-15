from fastapi import APIRouter
from core.supabase_client import supabase

router = APIRouter()

@router.get("/analytics/dashboard")
def dashboard():

    vendas = supabase.table("vendas").select("*").execute()

    return {
        "total_vendas": len(vendas.data)
    }
