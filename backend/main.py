from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Meta(BaseModel):
    periodo: str
    meta_faturamento: float
    meta_novos_clientes: int
    meta_reativacao: int
    meta_mix: int
    meta_share: float

metas = []

@app.get("/")
def status():
    return {"CTI": "Sistema ativo", "modulo": "Planejamento Comercial"}

@app.post("/metas")
def criar_meta(meta: Meta):
    metas.append(meta)
    return {"mensagem": "Meta registrada", "dados": meta}

@app.get("/metas")
def listar_metas():
    return metas
