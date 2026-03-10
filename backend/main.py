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

    vendas = supabase.table("vendas").select("*").execute()
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

    for v in vendas.data:

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
