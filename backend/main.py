from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client
import os

# ===============================
# BASE GLOBAL CTI
# ===============================

base_cti = []

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
# ============================================================
# ANALYTICS MODULE
# ============================================================

@app.get("/analytics/vendas-por-linha")
async def vendas_por_linha():

    vendas = supabase.table("vendas").select("*, equipamentos(linha)").execute()

    resultado = {}

    for v in vendas.data:
        linha = v["equipamentos"]["linha"]

        if linha not in resultado:
            resultado[linha] = {
                "linha": linha,
                "total_vendas": 0,
                "valor_total": 0
            }

        resultado[linha]["total_vendas"] += 1
        resultado[linha]["valor_total"] += v["valor"]

    return list(resultado.values())


@app.get("/analytics/ranking-clientes")
async def ranking_clientes():

    vendas = supabase.table("vendas").select("valor, clientes(nome)").execute()

    ranking = {}

    for v in vendas.data:

        cliente = v["clientes"]["nome"]

        if cliente not in ranking:
            ranking[cliente] = {
                "cliente": cliente,
                "total_vendas": 0,
                "valor_total": 0
            }

        ranking[cliente]["total_vendas"] += 1
        ranking[cliente]["valor_total"] += v["valor"]

    return sorted(ranking.values(), key=lambda x: x["valor_total"], reverse=True)


@app.get("/analytics/ranking-oem")
async def ranking_oem():

    vendas = supabase.table("vendas").select("valor, implementadores(nome)").execute()

    ranking = {}

    for v in vendas.data:

        oem = v["implementadores"]["nome"]

        if oem not in ranking:
            ranking[oem] = {
                "oem": oem,
                "total_vendas": 0,
                "valor_total": 0
            }

        ranking[oem]["total_vendas"] += 1
        ranking[oem]["valor_total"] += v["valor"]

    return sorted(ranking.values(), key=lambda x: x["valor_total"], reverse=True)


@app.get("/analytics/vendas-por-modelo")
async def vendas_por_modelo():

    vendas = supabase.table("vendas").select("valor, equipamentos(modelo)").execute()

    resultado = {}

    for v in vendas.data:

        modelo = v["equipamentos"]["modelo"]

        if modelo not in resultado:
            resultado[modelo] = {
                "modelo": modelo,
                "total_vendas": 0,
                "valor_total": 0
            }

        resultado[modelo]["total_vendas"] += 1
        resultado[modelo]["valor_total"] += v["valor"]

    return sorted(resultado.values(), key=lambda x: x["valor_total"], reverse=True)


@app.get("/analytics/vendas-por-estado")
async def vendas_por_estado():

    vendas = supabase.table("vendas").select("valor, clientes(estado)").execute()

    resultado = {}

    for v in vendas.data:

        estado = v["clientes"]["estado"]

        if estado not in resultado:
            resultado[estado] = {
                "estado": estado,
                "total_vendas": 0,
                "valor_total": 0
            }

        resultado[estado]["total_vendas"] += 1
        resultado[estado]["valor_total"] += v["valor"]

    return sorted(resultado.values(), key=lambda x: x["valor_total"], reverse=True)

# ============================================================
# SAFE ANALYTICS (fix for relations)
# ============================================================

@app.get("/analytics/vendas-por-linha-safe")
async def vendas_por_linha_safe():

    vendas = supabase.table("vendas").select("*").execute()
    equipamentos = supabase.table("equipamentos").select("*").execute()

    mapa_equipamentos = {e["id"]: e for e in equipamentos.data}

    resultado = {}

    for v in vendas.data:

        equipamento = mapa_equipamentos.get(v["equipamento_id"])

        if not equipamento:
            continue

        linha = equipamento["linha"]

        if linha not in resultado:
            resultado[linha] = {
                "linha": linha,
                "total_vendas": 0,
                "valor_total": 0
            }

        resultado[linha]["total_vendas"] += 1
        resultado[linha]["valor_total"] += v["valor"]

    return list(resultado.values())

# ============================================================
# INTELIGENCIA COMERCIAL
# ============================================================

@app.get("/analytics/inteligencia-comercial")
async def inteligencia_comercial():

    vendas = base_cti
    clientes = supabase.table("clientes").select("*").execute()
    equipamentos = supabase.table("equipamentos").select("*").execute()
    implementadores = supabase.table("implementadores").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}
    mapa_equipamentos = {e["id"]: e for e in equipamentos.data}
    mapa_oem = {i["id"]: i for i in implementadores.data}

    analise_estado = {}
    analise_linha = {}
    analise_oem = {}

    total_vendas = 0
    faturamento_total = 0

    for v in vendas:
        
        cliente = mapa_clientes.get(v["cliente_id"])
        equipamento = mapa_equipamentos.get(v["equipamento_id"])
        oem = mapa_oem.get(v["implementador_id"])

        if not cliente or not equipamento:
            continue

        estado = cliente["estado"]
        linha = equipamento["linha"]

        total_vendas += 1
        faturamento_total += v["valor"]

        # estado
        if estado not in analise_estado:
            analise_estado[estado] = {
                "estado": estado,
                "vendas": 0,
                "faturamento": 0
            }

        analise_estado[estado]["vendas"] += 1
        analise_estado[estado]["faturamento"] += v["valor"]

        # linha
        if linha not in analise_linha:
            analise_linha[linha] = {
                "linha": linha,
                "vendas": 0,
                "faturamento": 0
            }

        analise_linha[linha]["vendas"] += 1
        analise_linha[linha]["faturamento"] += v["valor"]

        # oem
        if oem:
            nome_oem = oem["nome"]

            if nome_oem not in analise_oem:
                analise_oem[nome_oem] = {
                    "oem": nome_oem,
                    "vendas": 0,
                    "faturamento": 0
                }

            analise_oem[nome_oem]["vendas"] += 1
            analise_oem[nome_oem]["faturamento"] += v["valor"]

    # oportunidades
    oportunidades = []

    for linha in analise_linha.values():

        if linha["vendas"] < 3:

            oportunidades.append({
                "tipo": "linha_subexplorada",
                "linha": linha["linha"],
                "observacao": "linha com baixa presença comercial"
            })

    return {
        "resumo_geral": {
            "total_vendas": total_vendas,
            "faturamento_total": faturamento_total
        },
        "performance_por_estado": list(analise_estado.values()),
        "performance_por_linha": list(analise_linha.values()),
        "ranking_oem": sorted(
            analise_oem.values(),
            key=lambda x: x["faturamento"],
            reverse=True
        ),
        "oportunidades_detectadas": oportunidades
    }

# ============================================================
# RADAR ESTRATEGICO DE MERCADO
# ============================================================

@app.get("/analytics/radar-mercado")
async def radar_mercado():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()
    equipamentos = supabase.table("equipamentos").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}
    mapa_equipamentos = {e["id"]: e for e in equipamentos.data}

    radar_estados = {}
    radar_linhas = {}

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])
        equipamento = mapa_equipamentos.get(v["equipamento_id"])

        if not cliente or not equipamento:
            continue

        estado = cliente["estado"]
        linha = equipamento["linha"]

        # radar por estado
        if estado not in radar_estados:
            radar_estados[estado] = {
                "estado": estado,
                "vendas": 0,
                "faturamento": 0
            }

        radar_estados[estado]["vendas"] += 1
        radar_estados[estado]["faturamento"] += v["valor"]

        # radar por linha
        if linha not in radar_linhas:
            radar_linhas[linha] = {
                "linha": linha,
                "vendas": 0,
                "faturamento": 0
            }

        radar_linhas[linha]["vendas"] += 1
        radar_linhas[linha]["faturamento"] += v["valor"]

    # identificar oportunidades
    oportunidades = []

    for estado in radar_estados.values():

        if estado["vendas"] <= 1:
            oportunidades.append({
                "tipo": "estado_subexplorado",
                "estado": estado["estado"],
                "observacao": "baixa presença comercial"
            })

    for linha in radar_linhas.values():

        if linha["vendas"] <= 2:
            oportunidades.append({
                "tipo": "linha_com_potencial",
                "linha": linha["linha"],
                "observacao": "linha com espaço de crescimento"
            })

    return {
        "radar_estados": list(radar_estados.values()),
        "radar_linhas": list(radar_linhas.values()),
        "oportunidades_detectadas": oportunidades
    }

# ============================================================
# RADAR COMERCIAL POR DDD (VIENA REGION)
# ============================================================

DDD_VIENA = ["011","012","013","014","015","018"]

@app.get("/analytics/radar-ddd")
async def radar_ddd():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()
    equipamentos = supabase.table("equipamentos").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}
    mapa_equipamentos = {e["id"]: e for e in equipamentos.data}

    radar_ddds = {}
    radar_linhas = {}

    total_vendas = 0
    faturamento_total = 0

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])
        equipamento = mapa_equipamentos.get(v["equipamento_id"])

        if not cliente or not equipamento:
            continue

        cidade = cliente.get("cidade","")

        # extrair DDD do cliente se existir
        ddd = cliente.get("ddd")

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        linha = equipamento["linha"]

        total_vendas += 1
        faturamento_total += v["valor"]

        # radar por DDD
        if ddd not in radar_ddds:
            radar_ddds[ddd] = {
                "ddd": ddd,
                "vendas": 0,
                "faturamento": 0
            }

        radar_ddds[ddd]["vendas"] += 1
        radar_ddds[ddd]["faturamento"] += v["valor"]

        # radar por linha
        if linha not in radar_linhas:
            radar_linhas[linha] = {
                "linha": linha,
                "vendas": 0,
                "faturamento": 0
            }

        radar_linhas[linha]["vendas"] += 1
        radar_linhas[linha]["faturamento"] += v["valor"]

    oportunidades = []

    for ddd in radar_ddds.values():

        if ddd["vendas"] <= 2:

            oportunidades.append({
                "tipo": "ddd_subexplorado",
                "ddd": ddd["ddd"],
                "observacao": "baixo volume de vendas na região"
            })

    return {
        "resumo_regional": {
            "total_vendas": total_vendas,
            "faturamento_total": faturamento_total
        },
        "radar_por_ddd": list(radar_ddds.values()),
        "radar_por_linha": list(radar_linhas.values()),
        "oportunidades_detectadas": oportunidades
    }

# ============================================================
# ANALYTICS POR DDD (VIENA REGION)
# ============================================================

DDD_VIENA = ["011","012","013","014","015","018"]


@app.get("/analytics/vendas-por-ddd")
async def vendas_por_ddd():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}

    resultado = {}

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])

        if not cliente:
            continue

        ddd = cliente.get("ddd")

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        if ddd not in resultado:
            resultado[ddd] = {
                "ddd": ddd,
                "total_vendas": 0,
                "valor_total": 0
            }

        resultado[ddd]["total_vendas"] += 1
        resultado[ddd]["valor_total"] += v["valor"]

    return sorted(resultado.values(), key=lambda x: x["valor_total"], reverse=True)


@app.get("/analytics/ranking-oem-por-ddd")
async def ranking_oem_por_ddd():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()
    implementadores = supabase.table("implementadores").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}
    mapa_oem = {i["id"]: i for i in implementadores.data}

    ranking = {}

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])
        oem = mapa_oem.get(v["implementador_id"])

        if not cliente or not oem:
            continue

        ddd = cliente.get("ddd")

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        chave = f"{ddd}-{oem['nome']}"

        if chave not in ranking:
            ranking[chave] = {
                "ddd": ddd,
                "oem": oem["nome"],
                "total_vendas": 0,
                "valor_total": 0
            }

        ranking[chave]["total_vendas"] += 1
        ranking[chave]["valor_total"] += v["valor"]

    return sorted(ranking.values(), key=lambda x: x["valor_total"], reverse=True)


@app.get("/analytics/vendas-por-linha-ddd")
async def vendas_por_linha_ddd():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()
    equipamentos = supabase.table("equipamentos").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}
    mapa_equipamentos = {e["id"]: e for e in equipamentos.data}

    resultado = {}

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])
        equipamento = mapa_equipamentos.get(v["equipamento_id"])

        if not cliente or not equipamento:
            continue

        ddd = cliente.get("ddd")

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        linha = equipamento["linha"]

        chave = f"{ddd}-{linha}"

        if chave not in resultado:
            resultado[chave] = {
                "ddd": ddd,
                "linha": linha,
                "total_vendas": 0,
                "valor_total": 0
            }

        resultado[chave]["total_vendas"] += 1
        resultado[chave]["valor_total"] += v["valor"]

    return sorted(resultado.values(), key=lambda x: x["valor_total"], reverse=True)


@app.get("/analytics/clientes-por-ddd")
async def clientes_por_ddd():

    clientes = supabase.table("clientes").select("*").execute()

    resultado = {}

    for c in clientes.data:

        ddd = c.get("ddd")

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        if ddd not in resultado:
            resultado[ddd] = {
                "ddd": ddd,
                "total_clientes": 0
            }

        resultado[ddd]["total_clientes"] += 1

    return sorted(resultado.values(), key=lambda x: x["total_clientes"], reverse=True)

# ============================================================
# BENCHMARK TERRITORIAL
# ============================================================

@app.get("/analytics/benchmark-territorial")
async def benchmark_territorial():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()
    equipamentos = supabase.table("equipamentos").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}
    mapa_equip = {e["id"]: e for e in equipamentos.data}

    total_brasil = 0
    total_sp = 0

    linhas_brasil = {}
    linhas_sp = {}

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])
        equip = mapa_equip.get(v["equipamento_id"])

        if not cliente or not equip:
            continue

        estado = cliente.get("estado")
        ddd = cliente.get("ddd")
        linha = equip.get("linha")

        total_brasil += v["valor"]

        linhas_brasil[linha] = linhas_brasil.get(linha, 0) + v["valor"]

        if ddd in DDD_VIENA:

            total_sp += v["valor"]

            linhas_sp[linha] = linhas_sp.get(linha, 0) + v["valor"]

    participacao_sp = 0

    if total_brasil > 0:
        participacao_sp = round((total_sp / total_brasil) * 100, 2)

    diferencas = []

    for linha in linhas_brasil:

        valor_br = linhas_brasil.get(linha, 0)
        valor_sp = linhas_sp.get(linha, 0)

        part_br = 0
        part_sp = 0

        if total_brasil > 0:
            part_br = round((valor_br / total_brasil) * 100, 2)

        if total_sp > 0:
            part_sp = round((valor_sp / total_sp) * 100, 2)

        diferencas.append({
            "linha": linha,
            "participacao_brasil": part_br,
            "participacao_sp": part_sp
        })

    return {
        "participacao_sp_no_brasil": participacao_sp,
        "comparativo_linhas": diferencas
    }

# ============================================================
# INTELIGENCIA DE MERCADO
# ============================================================

@app.get("/analytics/inteligencia-mercado")
async def inteligencia_mercado():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()
    equipamentos = supabase.table("equipamentos").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}
    mapa_equip = {e["id"]: e for e in equipamentos.data}

    linhas = {}
    ddds = {}

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])
        equip = mapa_equip.get(v["equipamento_id"])

        if not cliente or not equip:
            continue

        linha = equip.get("linha")
        ddd = cliente.get("ddd")

        linhas[linha] = linhas.get(linha, 0) + v["valor"]

        if ddd in DDD_VIENA:
            ddds[ddd] = ddds.get(ddd, 0) + v["valor"]

    linhas_ordenadas = sorted(linhas.items(), key=lambda x: x[1])
    ddd_ordenados = sorted(ddds.items(), key=lambda x: x[1])

    oportunidades = []

    if linhas_ordenadas:

        linha_fraca = linhas_ordenadas[0][0]

        oportunidades.append({
            "tipo": "linha_subexplorada",
            "linha": linha_fraca,
            "observacao": "linha com menor volume de vendas"
        })

    if ddd_ordenados:

        ddd_fraco = ddd_ordenados[0][0]

        oportunidades.append({
            "tipo": "territorio_subexplorado",
            "ddd": ddd_fraco,
            "observacao": "baixo volume de vendas na regiao"
        })

    return {
        "linhas_vendas": linhas,
        "ddd_vendas": ddds,
        "oportunidades_detectadas": oportunidades
    }

# ============================================================
# HEATMAP COMERCIAL POR DDD
# ============================================================

@app.get("/analytics/heatmap-comercial-ddd")
async def heatmap_comercial_ddd():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}

    ddd_stats = {}

    total_vendas = 0
    total_valor = 0

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])

        if not cliente:
            continue

        ddd = cliente.get("ddd")

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        if ddd not in ddd_stats:

            ddd_stats[ddd] = {
                "ddd": ddd,
                "total_vendas": 0,
                "valor_total": 0
            }

        ddd_stats[ddd]["total_vendas"] += 1
        ddd_stats[ddd]["valor_total"] += v["valor"]

        total_vendas += 1
        total_valor += v["valor"]

    resultado = []

    for ddd in ddd_stats:

        vendas_ddd = ddd_stats[ddd]["total_vendas"]
        valor_ddd = ddd_stats[ddd]["valor_total"]

        participacao = 0

        if total_valor > 0:
            participacao = round((valor_ddd / total_valor) * 100, 2)

        classificacao = "baixo"

        if participacao > 40:
            classificacao = "dominante"

        elif participacao > 20:
            classificacao = "forte"

        elif participacao > 10:
            classificacao = "moderado"

        resultado.append({
            "ddd": ddd,
            "total_vendas": vendas_ddd,
            "valor_total": valor_ddd,
            "participacao_regional": participacao,
            "classificacao": classificacao
        })

    return {
        "total_vendas_regiao": total_vendas,
        "faturamento_regiao": total_valor,
        "heatmap": sorted(resultado, key=lambda x: x["valor_total"], reverse=True)
    }

# ============================================================
# PROJECAO DE POTENCIAL DE MERCADO POR DDD
# ============================================================

@app.get("/analytics/projecao-mercado-ddd")
async def projecao_mercado_ddd():

    vendas = supabase.table("vendas").select("*").execute()
    clientes = supabase.table("clientes").select("*").execute()

    mapa_clientes = {c["id"]: c for c in clientes.data}

    ddd_stats = {}

    total_valor = 0

    for v in vendas.data:

        cliente = mapa_clientes.get(v["cliente_id"])

        if not cliente:
            continue

        ddd = cliente.get("ddd")

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        if ddd not in ddd_stats:

            ddd_stats[ddd] = {
                "ddd": ddd,
                "valor_total": 0
            }

        ddd_stats[ddd]["valor_total"] += v["valor"]

        total_valor += v["valor"]

    resultado = []

    for ddd in ddd_stats:

        valor = ddd_stats[ddd]["valor_total"]

        participacao = 0

        if total_valor > 0:
            participacao = round((valor / total_valor) * 100, 2)

        potencial_estimado = valor * 1.35

        crescimento_possivel = potencial_estimado - valor

        resultado.append({

            "ddd": ddd,
            "vendas_atuais": valor,
            "participacao_regional": participacao,
            "potencial_estimado": round(potencial_estimado,2),
            "crescimento_possivel": round(crescimento_possivel,2)

        })

    return sorted(resultado, key=lambda x: x["potencial_estimado"], reverse=True)

# ============================================================
# RADAR DE CLIENTES ESTRATÉGICOS
# ============================================================

@app.get("/analytics/radar-clientes")
def radar_clientes():

    query = """
    SELECT 
        cliente,
        cidade,
        ddd,
        COUNT(*) as total_compras,
        COUNT(DISTINCT fabricante) as fabricantes_diferentes,
        MIN(data_venda) as primeira_compra,
        MAX(data_venda) as ultima_compra
    FROM vendas
    GROUP BY cliente, cidade, ddd
    """

    result = supabase.rpc("execute_sql", {"query": query}).execute()

    clientes = result.data if result.data else []

    prioritarios = []
    fidelizados = []
    risco = []

    for c in clientes:

        if c["fabricantes_diferentes"] == 1 and c["total_compras"] >= 2:
            fidelizados.append(c)

        elif c["fabricantes_diferentes"] > 1:
            risco.append(c)

        else:
            prioritarios.append(c)

    return {
        "clientes_prioritarios": prioritarios,
        "clientes_fidelizados": fidelizados,
        "clientes_em_risco": risco
    }

# ============================================================
# ANALISE TEMPORAL DE CLIENTES
# ============================================================

@app.get("/analytics/clientes-recorrencia")
def clientes_recorrencia():

    query = """
    SELECT
        cliente,
        cidade,
        ddd,
        COUNT(*) as total_compras,
        EXTRACT(YEAR FROM MIN(data_venda)) as primeiro_ano,
        EXTRACT(YEAR FROM MAX(data_venda)) as ultimo_ano
    FROM vendas
    GROUP BY cliente, cidade, ddd
    """

    result = supabase.rpc("execute_sql", {"query": query}).execute()

    clientes = result.data if result.data else []

    for c in clientes:

        anos = (c["ultimo_ano"] - c["primeiro_ano"]) + 1
        if anos <= 0:
            anos = 1

        c["periodo_analise"] = f'{c["primeiro_ano"]}-{c["ultimo_ano"]}'
        c["media_anual"] = round(c["total_compras"] / anos, 2)

    return {
        "analise_clientes": clientes
    }

# ============================================================
# IMPORTADOR ANFIR
# ============================================================

import pandas as pd
from fastapi import UploadFile, File

@app.post("/upload/anfir")
async def upload_anfir(file: UploadFile = File(...)):

    import io

    contents = await file.read()

    excel = pd.ExcelFile(io.BytesIO(contents))
                         
    registros = []

    for aba in excel.sheet_names:

        df = pd.read_excel(excel, sheet_name=aba)

        for _, row in df.iterrows():

            cliente = row.get("cliente")
            cidade = row.get("cidade") or row.get("municipio")
            uf = row.get("uf")
            produto = row.get("produto")
            fabricante = row.get("fabricante")
            data = row.get("data")

            if not cliente or not cidade:
                continue

            registro = {
                "cliente": str(cliente),
                "cidade": str(cidade),
                "uf": str(uf),
                "produto": str(produto),
                "fabricante": str(fabricante),
                "data_venda": str(data)
            }

            registros.append(registro)

    if registros:
        supabase.table("vendas").insert(registros).execute()

    return {
        "status": "importado",
        "total_registros": len(registros)
    }

# ============================================================
# NORMALIZAÇÃO GEOGRÁFICA (CIDADE → DDD)
# ============================================================

def identificar_ddd(cidade):

    mapa_ddd = {
        "SAO PAULO": "011",
        "SANTOS": "013",
        "SOROCABA": "015",
        "BAURU": "014",
        "SAO JOSE DOS CAMPOS": "012",
        "ANDRADINA": "018"
    }

    if not cidade:
        return None

    cidade = cidade.upper().strip()

    return mapa_ddd.get(cidade)

# ============================================================
# CONSULTA GEOGRÁFICA CIDADE → DDD
# ============================================================

def buscar_ddd_por_cidade(cidade):

    if not cidade:
        return None

    cidade = cidade.upper().strip()

    response = supabase.table("cidades_ddd")\
        .select("ddd")\
        .ilike("cidade", cidade)\
        .execute()

    if response.data and len(response.data) > 0:
        return response.data[0]["ddd"]

    return None

# ---------------------------------------------------
# LIBERAÇÃO DE CORS PARA FRONTEND CTI
# ---------------------------------------------------

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# FIM BLOCO CORS
# ---------------------------------------------------

# ===============================
# LEITURA COMPLETA PLANILHA ANFIR
# ===============================

import io
import pandas as pd

def processar_planilha_anfir(contents):

    excel = pd.ExcelFile(io.BytesIO(contents))

    registros = []

    for aba in excel.sheet_names:

        df = pd.read_excel(excel, sheet_name=aba)

        df = df.dropna(how="all")

        for _, row in df.iterrows():

            cliente = row.get("cliente") or row.get("Cliente")
            cidade = row.get("cidade") or row.get("municipio") or row.get("Cidade")
            uf = row.get("uf") or row.get("UF")
            produto = row.get("produto") or row.get("Produto")
            fabricante = row.get("fabricante") or row.get("Fabricante")
            data = row.get("data") or row.get("Data")

            if cliente is None:
                continue

            registros.append({
                "cliente": str(cliente),
                "cidade": str(cidade),
                "uf": str(uf),
                "produto": str(produto),
                "fabricante": str(fabricante),
                "data": str(data)
            })

    return registros

# ===============================
# CONEXÃO DO UPLOAD COM O PARSER
# ===============================

@app.post("/upload/anfir/processado")
async def upload_anfir_processado(file: UploadFile = File(...)):

    contents = await file.read()

    registros = processar_planilha_anfir(contents)

    return {
        "status": "processado",
        "registros_lidos": len(registros),
        "amostra": registros[:5]
    }

# ===============================
# ARMAZENAMENTO TEMPORÁRIO CTI
# ===============================

@app.post("/upload/anfir/cti")
async def upload_anfir_cti(file: UploadFile = File(...)):

    contents = await file.read()

    registros = processar_planilha_anfir(contents)

    supabase.table("cti_anfir").insert(registros).execute()

    dados = supabase.table("cti_anfir").select("*").execute()

    return {
        "status": "dados inseridos no CTI",
        "total_registros": len(registros),
        "base_cti": len(dados.data)
    }

# ===============================
# ANALYTICS DO CTI
# ===============================

from collections import Counter

@app.get("/analytics/inteligencia-comercial")
def analytics_inteligencia_comercial():

    total_vendas = len(dados_anfir)

    estados = Counter()
    linhas = Counter()
    oems = Counter()

    for r in dados_anfir:

        uf = r.get("uf")
        produto = r.get("produto")
        fabricante = r.get("fabricante")

        if uf:
            estados[uf] += 1

        if produto:
            linhas[produto] += 1

        if fabricante:
            oems[fabricante] += 1

    performance_estado = [
        {"estado": k, "vendas": v}
        for k, v in estados.items()
    ]

    performance_linha = [
        {"linha": k, "vendas": v}
        for k, v in linhas.items()
    ]

    ranking_oem = [
        {"oem": k, "vendas": v}
        for k, v in oems.items()
    ]

    return {

        "resumo_geral": {
            "total_vendas": total_vendas,
            "faturamento_total": total_vendas * 100000
        },

        "performance_por_estado": performance_estado,
        "performance_por_linha": performance_linha,
        "ranking_oem": ranking_oem
    }

# ===============================
# ANALYTICS CTI CORRIGIDO
# ===============================

@app.get("/analytics/inteligencia-comercial")
def inteligencia_comercial():

    global base_cti

    total_vendas = len(base_cti)

    faturamento_total = sum(
        item.get("valor_total",0) for item in base_cti
    )

    performance_estado = {}
    performance_linha = {}
    ranking_oem = {}

    for item in base_cti:

        estado = item.get("estado","NA")
        linha = item.get("linha","NA")
        oem = item.get("oem","NA")
        valor = item.get("valor_total",0)

        # estado
        if estado not in performance_estado:
            performance_estado[estado] = {"estado":estado,"vendas":0,"faturamento":0}

        performance_estado[estado]["vendas"] += 1
        performance_estado[estado]["faturamento"] += valor

        # linha
        if linha not in performance_linha:
            performance_linha[linha] = {"linha":linha,"vendas":0,"faturamento":0}

        performance_linha[linha]["vendas"] += 1
        performance_linha[linha]["faturamento"] += valor

        # oem
        if oem not in ranking_oem:
            ranking_oem[oem] = {"oem":oem,"vendas":0,"faturamento":0}

        ranking_oem[oem]["vendas"] += 1
        ranking_oem[oem]["faturamento"] += valor

    return {
        "resumo_geral":{
            "total_vendas": total_vendas,
            "faturamento_total": faturamento_total
        },
        "performance_por_estado": list(performance_estado.values()),
        "performance_por_linha": list(performance_linha.values()),
        "ranking_oem": list(ranking_oem.values()),
        "oportunidades_detectadas":[]
    }

@app.get("/analytics/cti-debug")
def cti_debug():

    global base_cti

    return {
        "registros_na_base": len(base_cti)
    }
