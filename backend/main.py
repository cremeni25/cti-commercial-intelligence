from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client
import os

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class Meta(BaseModel):
    periodo: str
    meta_faturamento: float
    meta_novos_clientes: int
    meta_reativacao: int
    meta_mix: int
    meta_share: float


@app.get("/")
def status():
    return {"CTI": "Sistema ativo", "modulo": "Planejamento Comercial"}


@app.post("/metas")
def criar_meta(meta: Meta):

    data = {
        "periodo": meta.periodo,
        "meta_faturamento": meta.meta_faturamento,
        "meta_novos_clientes": meta.meta_novos_clientes,
        "meta_reativacao": meta.meta_reativacao,
        "meta_mix": meta.meta_mix,
        "meta_share": meta.meta_share
    }

    result = supabase.table("metas").insert(data).execute()

    return result.data


@app.get("/metas")
def listar_metas():

    result = supabase.table("metas").select("*").execute()

    return result.data
