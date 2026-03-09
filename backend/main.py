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


class Cliente(BaseModel):
    nome: str
    cidade: str
    estado: str
    segmento: str


@app.get("/")
def status():
    return {"CTI": "Sistema ativo"}


# ==============================
# METAS
# ==============================

@app.post("/metas")
def criar_meta(meta: Meta):

    result = supabase.table("metas").insert(meta.dict()).execute()

    return result.data


@app.get("/metas")
def listar_metas():

    result = supabase.table("metas").select("*").execute()

    return result.data


# ==============================
# CLIENTES
# ==============================

@app.post("/clientes")
def criar_cliente(cliente: Cliente):

    result = supabase.table("clientes").insert(cliente.dict()).execute()

    return result.data


@app.get("/clientes")
def listar_clientes():

    result = supabase.table("clientes").select("*").execute()

    return result.data


# ==============================
# MODULO OEM - IMPLEMENTADORES
# ==============================

class Implementador(BaseModel):
    nome: str
    estado: str | None = None
    tipo: str | None = None


@app.post("/implementadores")
def criar_implementador(implementador: Implementador):

    result = supabase.table("implementadores").insert(
        implementador.dict()
    ).execute()

    return result.data


@app.get("/implementadores")
def listar_implementadores():

    result = supabase.table("implementadores").select("*").execute()

    return result.data


# ==============================
# MODULO EQUIPAMENTOS
# ==============================

class Equipamento(BaseModel):
    linha: str
    modelo: str
    observacao: str | None = None


@app.post("/equipamentos")
def criar_equipamento(equipamento: Equipamento):

    result = supabase.table("equipamentos").insert(
        equipamento.dict()
    ).execute()

    return result.data


@app.get("/equipamentos")
def listar_equipamentos():

    result = supabase.table("equipamentos").select("*").execute()

    return result.data


# ==============================
# MODULO VENDAS
# ==============================

@app.get("/vendas")
def listar_vendas():

    response = supabase.table("vendas").select("*").execute()

    return response.data


@app.post("/vendas")
def criar_venda(payload: dict):

    venda = {
        "cliente_id": payload.get("cliente_id"),
        "equipamento_id": payload.get("equipamento_id"),
        "implementador_id": payload.get("implementador_id"),
        "tipo_venda": payload.get("tipo_venda"),
        "valor": payload.get("valor"),
        "data_venda": payload.get("data_venda"),
        "observacao": payload.get("observacao")
    }

    try:

        response = supabase.table("vendas").insert(venda).execute()

        return response.data

    except Exception as e:

        return {
            "erro": "Falha ao registrar venda",
            "detalhe": str(e),
            "payload": venda
        }


@app.get("/vendas/{venda_id}")
def buscar_venda(venda_id: str):

    response = supabase.table("vendas").select("*").eq("id", venda_id).execute()

    return response.data


@app.delete("/vendas/{venda_id}")
def deletar_venda(venda_id: str):

    response = supabase.table("vendas").delete().eq("id", venda_id).execute()

    return {"deleted": venda_id}


# ==============================
# CORREÇÃO OPERACIONAL VENDAS
# ==============================

@app.post("/vendas2")
async def criar_venda_corrigida(payload: dict):

    venda = {
        "cliente_id": payload.get("cliente_id"),
        "equipamento_id": payload.get("equipamento_id"),
        "implementador_id": payload.get("implementador_id"),
        "tipo_venda": payload.get("tipo_venda"),
        "valor": payload.get("valor"),
        "data_venda": payload.get("data_venda"),
        "observacao": payload.get("observacao")
    }

    try:

        response = supabase.table("vendas").insert(venda).execute()

        return response.data

    except Exception as e:

        return {
            "erro": "Falha ao registrar venda",
            "detalhe": str(e),
            "payload": venda
        }

# ============================================================
# ANALYTICS MODULE
# ============================================================

@app.get("/analytics/vendas-por-linha")
async def vendas_por_linha():

    query = """
    select
        e.linha,
        count(v.id) as total_vendas,
        sum(v.valor) as valor_total
    from vendas v
    join equipamentos e on v.equipamento_id = e.id
    group by e.linha
    order by valor_total desc
    """

    result = supabase.rpc("execute_sql", {"query": query}).execute()

    return result.data


@app.get("/analytics/vendas-por-modelo")
async def vendas_por_modelo():

    query = """
    select
        e.modelo,
        e.linha,
        count(v.id) as total_vendas,
        sum(v.valor) as valor_total
    from vendas v
    join equipamentos e on v.equipamento_id = e.id
    group by e.modelo, e.linha
    order by valor_total desc
    """

    result = supabase.rpc("execute_sql", {"query": query}).execute()

    return result.data


@app.get("/analytics/ranking-clientes")
async def ranking_clientes():

    query = """
    select
        c.nome,
        c.estado,
        count(v.id) as total_vendas,
        sum(v.valor) as valor_total
    from vendas v
    join clientes c on v.cliente_id = c.id
    group by c.nome, c.estado
    order by valor_total desc
    """

    result = supabase.rpc("execute_sql", {"query": query}).execute()

    return result.data


@app.get("/analytics/ranking-oem")
async def ranking_oem():

    query = """
    select
        i.nome,
        i.estado,
        i.tipo,
        count(v.id) as total_vendas,
        sum(v.valor) as valor_total
    from vendas v
    join implementadores i on v.implementador_id = i.id
    group by i.nome, i.estado, i.tipo
    order by valor_total desc
    """

    result = supabase.rpc("execute_sql", {"query": query}).execute()

    return result.data


@app.get("/analytics/vendas-por-estado")
async def vendas_por_estado():

    query = """
    select
        c.estado,
        count(v.id) as total_vendas,
        sum(v.valor) as valor_total
    from vendas v
    join clientes c on v.cliente_id = c.id
    group by c.estado
    order by valor_total desc
    """

    result = supabase.rpc("execute_sql", {"query": query}).execute()

    return result.data
