# ============================================================
# CTI BACKEND V2
# CORE SYSTEM
# ============================================================

from routers.clientes_router import router as clientes_router
from routers.vendas_router import router as vendas_router
from routers.negociacoes_router import router as negociacoes_router
from routers.analytics_router import router as analytics_router
from core.config import APP_NAME, APP_VERSION
from fastapi import FastAPI, UploadFile, File
from routers.upload_router import router as upload_router
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
import pandas as pd
import os
import io
import re
from datetime import datetime
from engine.market_engine import MarketEngine
from engine.win_loss_engine import WinLossEngine
from core.supabase_client import supabase
from routers.engine_router import router as engine_router

# ============================================================
# INICIALIZAÇÃO FASTAPI
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)
app.include_router(upload_router)
app.include_router(clientes_router)
app.include_router(vendas_router)
app.include_router(negociacoes_router)
app.include_router(analytics_router)
app.include_router(engine_router)

# ============================================================
# CORS (frontend GitHub Pages)
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CONEXÃO SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# LOGS DO SISTEMA
# ============================================================

def log(msg):

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[CTI] {agora} | {msg}")

# ============================================================
# PAGINAÇÃO AUTOMÁTICA SUPABASE
# Remove limite de 1000 registros
# ============================================================

def select_all(table_name):

    page_size = 1000
    offset = 0
    resultados = []

    while True:

        response = supabase.table(table_name)\
            .select("*")\
            .range(offset, offset + page_size - 1)\
            .execute()

        data = response.data

        if not data:
            break

        resultados.extend(data)

        if len(data) < page_size:
            break

        offset += page_size

    return resultados

# ============================================================
# LIMPEZA DE DADOS
# remove NAN e valores inválidos
# ============================================================

def limpar_valor(v):

    try:

        if v is None:
            return 0

        if pd.isna(v):
            return 0

        return float(v)

    except:

        return 0

# ============================================================
# NORMALIZAÇÃO DE TEXTO
# ============================================================

def normalizar_texto(txt):

    if not txt:
        return ""

    txt = str(txt).strip().upper()

    txt = re.sub(r"\s+", " ", txt)

    return txt

# ============================================================
# DETECÇÃO AUTOMÁTICA DE IDENTIFICADOR
# (PLACA / CNPJ / NOME)
# ============================================================

def detectar_identificador(valor):

    if not valor:
        return "NOME"

    numeros = re.sub(r"\D", "", str(valor))

    if len(numeros) == 14:
        return "CNPJ"

    if len(valor) >= 7 and any(c.isalpha() for c in valor):
        return "PLACA"

    return "NOME"

# ============================================================
# STATUS DA API
# ============================================================

@app.get("/")
def status():

    return {
        "sistema": APP_NAME,
        "versao": APP_VERSION,
        "status": "ativo"
    }

# ============================================================
# MODELOS DE DADOS (Pydantic)
# ============================================================

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
    segmento: str | None = None
    cnpj: str | None = None


class Equipamento(BaseModel):

    linha: str
    modelo: str
    observacao: str | None = None


class Implementador(BaseModel):

    nome: str
    estado: str | None = None
    tipo: str | None = None


class Veiculo(BaseModel):

    placa: str
    cliente: str
    cnpj: str | None = None
    cidade: str | None = None
    estado: str | None = None


# ============================================================
# ROTAS DE METAS
# ============================================================

@app.post("/metas")
def criar_meta(meta: Meta):

    result = supabase.table("metas").insert(meta.dict()).execute()

    return result.data


@app.get("/metas")
def listar_metas():

    result = supabase.table("metas").select("*").execute()

    return result.data


# ============================================================
# ROTAS DE CLIENTES
# ============================================================

@app.post("/clientes")
def criar_cliente(cliente: Cliente):

    result = supabase.table("clientes").insert(cliente.dict()).execute()

    return result.data


@app.get("/clientes")
def listar_clientes():

    result = supabase.table("clientes").select("*").execute()

    return result.data


# ============================================================
# ROTAS DE IMPLEMENTADORES (OEM)
# ============================================================

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


# ============================================================
# ROTAS DE EQUIPAMENTOS
# ============================================================

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


# ============================================================
# BASE DE VEÍCULOS (RESOLUÇÃO DE PLACA)
# ============================================================

@app.post("/veiculos")
def criar_veiculo(veiculo: Veiculo):

    result = supabase.table("veiculos").insert(
        veiculo.dict()
    ).execute()

    return result.data


@app.get("/veiculos")
def listar_veiculos():

    result = supabase.table("veiculos").select("*").execute()

    return result.data

# ============================================================
# MODULO DE VENDAS
# ============================================================

class Venda(BaseModel):

    cliente_id: str
    equipamento_id: str
    implementador_id: str
    tipo_venda: str | None = None
    valor: float
    data_venda: str
    observacao: str | None = None


# ============================================================
# LISTAR VENDAS
# ============================================================

@app.get("/vendas")
def listar_vendas():

    vendas = select_all("vendas")

    return vendas


# ============================================================
# BUSCAR VENDA ESPECÍFICA
# ============================================================

@app.get("/vendas/{venda_id}")
def buscar_venda(venda_id: str):

    response = supabase.table("vendas")\
        .select("*")\
        .eq("id", venda_id)\
        .execute()

    return response.data


# ============================================================
# CRIAR VENDA
# ============================================================

@app.post("/vendas")
def criar_venda(venda: Venda):

    payload = venda.dict()

    payload["valor"] = limpar_valor(payload.get("valor"))

    try:

        response = supabase.table("vendas")\
            .insert(payload)\
            .execute()

        log("Venda registrada")

        return response.data

    except Exception as e:

        return {
            "erro": "Falha ao registrar venda",
            "detalhe": str(e),
            "payload": payload
        }

# ============================================================
# DELETAR VENDA
# ============================================================

@app.delete("/vendas/{venda_id}")
def deletar_venda(venda_id: str):

    response = supabase.table("vendas")\
        .delete()\
        .eq("id", venda_id)\
        .execute()

    return {
        "deleted": venda_id
    }

# ============================================================
# CORREÇÃO OPERACIONAL DE VENDAS
# ============================================================

@app.post("/vendas/corrigir")
def corrigir_venda(payload: dict):

    venda = {
        "cliente_id": payload.get("cliente_id"),
        "equipamento_id": payload.get("equipamento_id"),
        "implementador_id": payload.get("implementador_id"),
        "tipo_venda": payload.get("tipo_venda"),
        "valor": limpar_valor(payload.get("valor")),
        "data_venda": payload.get("data_venda"),
        "observacao": payload.get("observacao")
    }

    try:

        response = supabase.table("vendas")\
            .insert(venda)\
            .execute()

        log("Venda corrigida inserida")

        return response.data

    except Exception as e:

        return {
            "erro": "Falha na correção da venda",
            "detalhe": str(e),
            "payload": venda
        }

# ============================================================
# RESUMO OPERACIONAL DE VENDAS
# ============================================================

@app.get("/vendas/resumo")
def resumo_vendas():

    vendas = select_all("vendas")

    total_vendas = len(vendas)

    faturamento = 0

    for v in vendas:

        faturamento += limpar_valor(v.get("valor"))

    return {

        "total_vendas": total_vendas,
        "faturamento_total": faturamento

    }

# ============================================================
# ENGINE UNIVERSAL DE PLANILHAS
# ============================================================

def detectar_coluna(df, palavras):

    for coluna in df.columns:

        for p in palavras:

            if p in coluna:

                return coluna

    return None

# ============================================================
# PROCESSADOR UNIVERSAL DE PLANILHAS
# ============================================================

def processar_planilha_universal(contents):

    df = pd.read_excel(io.BytesIO(contents))

    df = df.fillna("")

    # normalizar nomes das colunas
    df.columns = [normalizar_texto(c) for c in df.columns]

    registros = []

    # palavras chave possíveis
    colunas_estado = ["UF", "ESTADO"]
    colunas_cidade = ["CIDADE", "MUNICIPIO"]
    colunas_linha = ["LINHA", "PRODUTO", "IMPLEMENTO", "TIPO"]
    colunas_fabricante = ["FABRICANTE", "MARCA", "OEM", "IMPLEMENTADOR"]
    colunas_valor = ["VALOR", "TOTAL", "PRECO", "UNIT"]
    colunas_cliente = ["CLIENTE", "RAZAO", "EMPRESA"]
    colunas_cnpj = ["CNPJ"]
    colunas_placa = ["PLACA", "VEICULO"]

    col_estado = detectar_coluna(df, colunas_estado)
    col_cidade = detectar_coluna(df, colunas_cidade)
    col_linha = detectar_coluna(df, colunas_linha)
    col_fabricante = detectar_coluna(df, colunas_fabricante)
    col_valor = detectar_coluna(df, colunas_valor)
    col_cliente = detectar_coluna(df, colunas_cliente)
    col_cnpj = detectar_coluna(df, colunas_cnpj)
    col_placa = detectar_coluna(df, colunas_placa)

    for _, row in df.iterrows():

        estado = normalizar_texto(row.get(col_estado)) if col_estado else ""
        cidade = normalizar_texto(row.get(col_cidade)) if col_cidade else ""
        linha = normalizar_texto(row.get(col_linha)) if col_linha else ""
        fabricante = normalizar_texto(row.get(col_fabricante)) if col_fabricante else ""
        cliente = normalizar_texto(row.get(col_cliente)) if col_cliente else ""
        cnpj = row.get(col_cnpj) if col_cnpj else ""
        placa = normalizar_texto(row.get(col_placa)) if col_placa else ""

        valor = limpar_valor(row.get(col_valor)) if col_valor else 0

        identificador = None
        tipo_id = None

        if placa:

            identificador = placa
            tipo_id = "PLACA"

        elif cnpj:

            identificador = re.sub(r"\D", "", str(cnpj))
            tipo_id = "CNPJ"

        elif cliente:

            identificador = cliente
            tipo_id = "NOME"

        registros.append({

            "estado": estado,
            "cidade": cidade,
            "linha": linha,
            "fabricante": fabricante,
            "cliente": cliente,
            "cnpj": cnpj,
            "placa": placa,
            "identificador": identificador,
            "tipo_identificador": tipo_id,
            "valor": valor

        })

    return registros

# ============================================================
# UPLOAD UNIVERSAL DE PLANILHAS
# ============================================================

@app.post("/upload/universal")
async def upload_universal(file: UploadFile = File(...)):

    contents = await file.read()

    registros = processar_planilha_universal(contents)

    return {

        "status": "processado",
        "registros_lidos": len(registros),
        "amostra": registros[:5]

    }

# ============================================================
# MONITORAMENTO ANFIR
# ============================================================

def resolver_cliente_por_placa(placa):

    if not placa:
        return None

    response = supabase.table("veiculos")\
        .select("*")\
        .eq("placa", placa)\
        .execute()

    if response.data and len(response.data) > 0:

        return response.data[0]

    return None


def resolver_cliente_por_cnpj(cnpj):

    if not cnpj:
        return None

    cnpj = re.sub(r"\D", "", str(cnpj))

    response = supabase.table("clientes")\
        .select("*")\
        .eq("cnpj", cnpj)\
        .execute()

    if response.data and len(response.data) > 0:

        return response.data[0]

    return None

def resolver_cliente_por_nome(nome):

    if not nome:
        return None

    nome = normalizar_texto(nome)

    response = supabase.table("clientes")\
        .select("*")\
        .ilike("nome", f"%{nome}%")\
        .execute()

    if response.data and len(response.data) > 0:

        return response.data[0]

    return None

# ============================================================
# ENRIQUECIMENTO DE REGISTROS ANFIR
# ============================================================

def enriquecer_registro_anfir(registro):

    cliente_resolvido = None

    if registro["tipo_identificador"] == "PLACA":

        cliente_resolvido = resolver_cliente_por_placa(registro["placa"])

    elif registro["tipo_identificador"] == "CNPJ":

        cliente_resolvido = resolver_cliente_por_cnpj(registro["cnpj"])

    elif registro["tipo_identificador"] == "NOME":

        cliente_resolvido = resolver_cliente_por_nome(registro["cliente"])

    if cliente_resolvido:

        registro["cliente_resolvido"] = cliente_resolvido.get("nome")
        registro["cnpj_resolvido"] = cliente_resolvido.get("cnpj")

    else:

        registro["cliente_resolvido"] = None
        registro["cnpj_resolvido"] = None

    registro["data_processamento"] = datetime.now().strftime("%Y-%m-%d")

    return registro

# ============================================================
# PROCESSAR PRINTS ANFIR
# ============================================================

@app.post("/upload/anfir-monitoramento")
async def upload_anfir_monitoramento(file: UploadFile = File(...)):

    contents = await file.read()

    registros = processar_planilha_universal(contents)

    registros_enriquecidos = []

    for r in registros:

        enriquecido = enriquecer_registro_anfir(r)

        registros_enriquecidos.append(enriquecido)

    batch_size = 500

    for i in range(0, len(registros_enriquecidos), batch_size):

        batch = registros_enriquecidos[i:i + batch_size]

        supabase.table("anfir_monitoramento")\
            .insert(batch)\
            .execute()

    log(f"ANFIR monitoramento inserido: {len(registros_enriquecidos)} registros")

    return {

        "status": "monitoramento atualizado",
        "registros_processados": len(registros_enriquecidos)

    }

# ============================================================
# CONSULTA MONITORAMENTO ANFIR
# ============================================================

@app.get("/anfir/monitoramento")
def consultar_monitoramento():

    registros = select_all("anfir_monitoramento")

    return registros

# ============================================================
# MOTOR DE ANALYTICS
# ============================================================

@app.get("/analytics/inteligencia-comercial")
def inteligencia_comercial(ano: int = None, mes: int = None):

    # ========================================================
    # LEITURA DA BASE CTI (ANFIR)
    # ========================================================

    query = supabase.table("cti_anfir").select("*")

    if ano:
        query = query.eq("ano", ano)

    if mes:
        query = query.eq("mes", mes)

    data = query.execute().data
    
    vendas = select_all("cti_anfir")

    analise_estado = {}
    analise_linha = {}
    analise_oem = {}

    total_vendas = 0
    faturamento_total = 0

    for v in vendas:

        estado = normalizar_texto(v.get("estado"))
        linha = normalizar_texto(v.get("linha"))
        oem = normalizar_texto(v.get("implementador"))

        valor = limpar_valor(v.get("valor"))

        total_vendas += 1
        faturamento_total += valor

        # ----------------------------------------------------
        # ANALISE POR ESTADO
        # ----------------------------------------------------

        if estado not in analise_estado:

            analise_estado[estado] = {
                "estado": estado,
                "vendas": 0,
                "faturamento": 0
            }

        analise_estado[estado]["vendas"] += 1
        analise_estado[estado]["faturamento"] += valor

        # ----------------------------------------------------
        # ANALISE POR LINHA
        # ----------------------------------------------------

        if linha not in analise_linha:

            analise_linha[linha] = {
                "linha": linha,
                "vendas": 0,
                "faturamento": 0
            }

        analise_linha[linha]["vendas"] += 1
        analise_linha[linha]["faturamento"] += valor

        # ----------------------------------------------------
        # ANALISE OEM
        # ----------------------------------------------------

        if oem not in analise_oem:

            analise_oem[oem] = {
                "oem": oem,
                "vendas": 0,
                "faturamento": 0
            }

        analise_oem[oem]["vendas"] += 1
        analise_oem[oem]["faturamento"] += valor

    # ========================================================
    # DETECÇÃO DE OPORTUNIDADES
    # ========================================================

    oportunidades = []

    for linha in analise_linha.values():

        if linha["vendas"] <= 2:

            oportunidades.append({

                "tipo": "linha_subexplorada",
                "linha": linha["linha"],
                "observacao": "linha com baixa presença comercial"

            })

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

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
# RADAR DE MERCADO
# ============================================================

@app.get("/analytics/radar-mercado")
def radar_mercado():

    vendas = select_all("cti_anfir")

    radar_estados = {}
    radar_linhas = {}

    for v in vendas:

        estado = normalizar_texto(v.get("estado"))
        linha = normalizar_texto(v.get("linha"))

        valor = limpar_valor(v.get("valor"))

        # ----------------------------------------------------
        # RADAR ESTADOS
        # ----------------------------------------------------

        if estado not in radar_estados:

            radar_estados[estado] = {
                "estado": estado,
                "vendas": 0,
                "faturamento": 0
            }

        radar_estados[estado]["vendas"] += 1
        radar_estados[estado]["faturamento"] += valor

        # ----------------------------------------------------
        # RADAR LINHAS
        # ----------------------------------------------------

        if linha not in radar_linhas:

            radar_linhas[linha] = {
                "linha": linha,
                "vendas": 0,
                "faturamento": 0
            }

        radar_linhas[linha]["vendas"] += 1
        radar_linhas[linha]["faturamento"] += valor

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

                "tipo": "linha_subexplorada",
                "linha": linha["linha"],
                "observacao": "linha com espaço de crescimento"

            })

    return {

        "radar_estados": list(radar_estados.values()),
        "radar_linhas": list(radar_linhas.values()),
        "oportunidades_detectadas": oportunidades

    }


# ============================================================
# RADAR COMERCIAL POR DDD
# ============================================================

DDD_VIENA = ["011", "012", "013", "014", "015", "018"]

@app.get("/analytics/radar-ddd")
def radar_ddd():

    vendas = select_all("cti_anfir")

    radar_ddds = {}

    for v in vendas:

        cidade = normalizar_texto(v.get("cidade"))
        linha = normalizar_texto(v.get("linha"))

        ddd = v.get("ddd")

        valor = limpar_valor(v.get("valor"))

        if not ddd:
            continue

        if ddd not in DDD_VIENA:
            continue

        if ddd not in radar_ddds:

            radar_ddds[ddd] = {

                "ddd": ddd,
                "vendas": 0,
                "faturamento": 0

            }

        radar_ddds[ddd]["vendas"] += 1
        radar_ddds[ddd]["faturamento"] += valor

    oportunidades = []

    for ddd in radar_ddds.values():

        if ddd["vendas"] <= 2:

            oportunidades.append({

                "tipo": "ddd_subexplorado",
                "ddd": ddd["ddd"],
                "observacao": "baixo volume de vendas na região"

            })

    return {

        "radar_por_ddd": list(radar_ddds.values()),
        "oportunidades_detectadas": oportunidades

    }

# ============================================================
# HEATMAP COMERCIAL
# ============================================================

@app.get("/analytics/heatmap-comercial")
def heatmap_comercial():

    vendas = select_all("cti_anfir")

    mapa = {}

    total_valor = 0

    for v in vendas:

        estado = normalizar_texto(v.get("estado"))

        valor = limpar_valor(v.get("valor"))

        total_valor += valor

        if estado not in mapa:

            mapa[estado] = {

                "estado": estado,
                "valor_total": 0,
                "participacao": 0

            }

        mapa[estado]["valor_total"] += valor

    resultado = []

    for estado in mapa:

        valor = mapa[estado]["valor_total"]

        participacao = 0

        if total_valor > 0:

            participacao = round((valor / total_valor) * 100, 2)

        resultado.append({

            "estado": estado,
            "valor_total": valor,
            "participacao": participacao

        })

    return sorted(resultado, key=lambda x: x["valor_total"], reverse=True)

# ============================================================
# PROJEÇÃO DE POTENCIAL DE MERCADO
# ============================================================

@app.get("/analytics/projecao-mercado")
def projecao_mercado():

    vendas = select_all("cti_anfir")

    linhas = {}

    total_valor = 0

    for v in vendas:

        linha = normalizar_texto(v.get("linha"))

        valor = limpar_valor(v.get("valor"))

        total_valor += valor

        linhas[linha] = linhas.get(linha, 0) + valor

    resultado = []

    for linha in linhas:

        valor = linhas[linha]

        potencial = valor * 1.35

        crescimento = potencial - valor

        resultado.append({

            "linha": linha,
            "vendas_atuais": valor,
            "potencial_estimado": round(potencial, 2),
            "crescimento_possivel": round(crescimento, 2)

        })

    return sorted(resultado, key=lambda x: x["potencial_estimado"], reverse=True)

# ============================================================
# RADAR DE CLIENTES ESTRATÉGICOS
# ============================================================

@app.get("/analytics/radar-clientes")
def radar_clientes():

    vendas = select_all("vendas")
    clientes = select_all("clientes")

    mapa_clientes = {c["id"]: c for c in clientes}

    estatisticas = {}

    for v in vendas:

        cliente_id = v.get("cliente_id")

        if not cliente_id:
            continue

        cliente = mapa_clientes.get(cliente_id)

        if not cliente:
            continue

        nome = normalizar_texto(cliente.get("nome"))

        if nome not in estatisticas:

            estatisticas[nome] = {

                "cliente": nome,
                "total_compras": 0,
                "faturamento": 0

            }

        estatisticas[nome]["total_compras"] += 1
        estatisticas[nome]["faturamento"] += limpar_valor(v.get("valor"))

    prioritarios = []
    fidelizados = []
    risco = []

    for c in estatisticas.values():

        compras = c["total_compras"]

        if compras >= 5:

            prioritarios.append(c)

        elif compras >= 2:

            fidelizados.append(c)

        else:

            risco.append(c)

    return {

        "clientes_prioritarios": sorted(
            prioritarios,
            key=lambda x: x["faturamento"],
            reverse=True
        ),

        "clientes_fidelizados": sorted(
            fidelizados,
            key=lambda x: x["faturamento"],
            reverse=True
        ),

        "clientes_em_risco": sorted(
            risco,
            key=lambda x: x["faturamento"],
            reverse=True
        )

    }

# ============================================================
# ANÁLISE DE RECORRÊNCIA DE CLIENTES
# ============================================================

@app.get("/analytics/clientes-recorrencia")
def clientes_recorrencia():

    vendas = select_all("vendas")
    clientes = select_all("clientes")

    mapa_clientes = {c["id"]: c for c in clientes}

    historico = {}

    for v in vendas:

        cliente_id = v.get("cliente_id")

        if not cliente_id:
            continue

        cliente = mapa_clientes.get(cliente_id)

        if not cliente:
            continue

        nome = normalizar_texto(cliente.get("nome"))

        data = v.get("data_venda")

        if not data:
            continue

        ano = str(data)[:4]

        if nome not in historico:

            historico[nome] = {

                "cliente": nome,
                "primeiro_ano": ano,
                "ultimo_ano": ano,
                "total_compras": 0

            }

        historico[nome]["total_compras"] += 1

        if ano < historico[nome]["primeiro_ano"]:

            historico[nome]["primeiro_ano"] = ano

        if ano > historico[nome]["ultimo_ano"]:

            historico[nome]["ultimo_ano"] = ano

    resultado = []

    for c in historico.values():

        primeiro = int(c["primeiro_ano"])
        ultimo = int(c["ultimo_ano"])

        anos = (ultimo - primeiro) + 1

        if anos <= 0:

            anos = 1

        media = round(c["total_compras"] / anos, 2)

        resultado.append({

            "cliente": c["cliente"],
            "periodo": f"{primeiro}-{ultimo}",
            "total_compras": c["total_compras"],
            "media_anual": media

        })

    return sorted(resultado, key=lambda x: x["total_compras"], reverse=True)

# ============================================================
# MODELO DE NEGOCIAÇÃO
# ============================================================

class Negociacao(BaseModel):

    cliente: str
    cidade: str | None = None
    estado: str | None = None
    produto: str | None = None
    valor: float | None = None
    status: str | None = None
    data: str | None = None
    observacao: str | None = None

# ============================================================
# REGISTRAR NEGOCIAÇÃO
# ============================================================

@app.post("/negociacoes")
def criar_negociacao(negociacao: Negociacao):

    payload = negociacao.dict()

    payload["cliente"] = normalizar_texto(payload.get("cliente"))

    payload["valor"] = limpar_valor(payload.get("valor"))

    response = supabase.table("negociacoes")\
        .insert(payload)\
        .execute()

    log("Nova negociação registrada")

    return response.data

# ============================================================
# LISTAR NEGOCIAÇÕES
# ============================================================

@app.get("/negociacoes")
def listar_negociacoes():

    negociacoes = select_all("negociacoes")

    return negociacoes


# ============================================================
# RESUMO DO PIPELINE COMERCIAL
# ============================================================

@app.get("/analytics/pipeline")
def pipeline_comercial():

    negociacoes = select_all("negociacoes")

    pipeline_total = 0

    por_status = {}

    for n in negociacoes:

        status = normalizar_texto(n.get("status"))

        valor = limpar_valor(n.get("valor"))

        pipeline_total += valor

        if status not in por_status:

            por_status[status] = {

                "status": status,
                "negociacoes": 0,
                "valor_total": 0

            }

        por_status[status]["negociacoes"] += 1
        por_status[status]["valor_total"] += valor

    return {

        "pipeline_total": pipeline_total,

        "pipeline_por_status": list(por_status.values())

    }

# ============================================================
# MODELO DE CONTATO
# ============================================================

class Contato(BaseModel):

    cliente: str
    cargo: str | None = None
    telefone: str | None = None
    email: str | None = None
    relacionamento: str | None = None
    observacoes: str | None = None

# ============================================================
# REGISTRAR CONTATO
# ============================================================

@app.post("/contatos")
def criar_contato(contato: Contato):

    payload = contato.dict()

    payload["cliente"] = normalizar_texto(payload.get("cliente"))

    response = supabase.table("contatos")\
        .insert(payload)\
        .execute()

    log("Contato registrado")

    return response.data

# ============================================================
# LISTAR CONTATOS
# ============================================================

@app.get("/contatos")
def listar_contatos():

    contatos = select_all("contatos")

    return contatos

# ============================================================
# CLIENTES COM NEGOCIAÇÃO ATIVA
# ============================================================

@app.get("/analytics/clientes-negociacao")
def clientes_em_negociacao():

    negociacoes = select_all("negociacoes")

    clientes = {}

    for n in negociacoes:

        cliente = normalizar_texto(n.get("cliente"))

        valor = limpar_valor(n.get("valor"))

        if cliente not in clientes:

            clientes[cliente] = {

                "cliente": cliente,
                "negociacoes": 0,
                "valor_total": 0

            }

        clientes[cliente]["negociacoes"] += 1
        clientes[cliente]["valor_total"] += valor

    return sorted(

        clientes.values(),
        key=lambda x: x["valor_total"],
        reverse=True

    )

# ============================================================
# DASHBOARD MASTER CTI
# ============================================================

@app.get("/analytics/dashboard")
def dashboard_master():

    vendas = select_all("vendas")
    clientes = select_all("clientes")
    negociacoes = select_all("negociacoes")
    equipamentos = select_all("equipamentos")

    total_vendas = len(vendas)

    faturamento = sum(limpar_valor(v.get("valor")) for v in vendas)

    pipeline = sum(limpar_valor(n.get("valor")) for n in negociacoes)

    clientes_ativos = len(clientes)

    linhas = {}

    for v in vendas:

        equip_id = v.get("equipamento_id")

        if not equip_id:
            continue

        equip = next((e for e in equipamentos if e["id"] == equip_id), None)

        if not equip:
            continue

        linha = normalizar_texto(equip.get("linha"))

        if linha not in linhas:

            linhas[linha] = {

                "linha": linha,
                "vendas": 0,
                "valor": 0

            }

        linhas[linha]["vendas"] += 1

        linhas[linha]["valor"] += limpar_valor(v.get("valor"))

    ranking_linhas = sorted(

        linhas.values(),
        key=lambda x: x["valor"],
        reverse=True

    )

    return {

        "resumo": {

            "total_vendas": total_vendas,
            "faturamento": faturamento,
            "pipeline": pipeline,
            "clientes": clientes_ativos

        },

        "ranking_linhas": ranking_linhas

    }

# ============================================================
# STATUS DO SISTEMA
# ============================================================

@app.get("/cti/status")
def status_cti():

    try:

        clientes = select_all("clientes")
        vendas = select_all("vendas")
        negociacoes = select_all("negociacoes")

        return {

            "sistema": "CTI",
            "status": "operacional",

            "modulos": {

                "clientes": len(clientes),
                "vendas": len(vendas),
                "negociacoes": len(negociacoes)

            }

        }

    except Exception as e:

        return {

            "sistema": "CTI",
            "status": "erro",
            "detalhe": str(e)

        }

# ============================================================
# HEALTHCHECK PARA RENDER
# ============================================================

@app.get("/health")
def health():

    return {"status": "ok"}


# ============================================================
# INFORMAÇÕES DO SISTEMA
# ============================================================

@app.get("/cti/info")
def info_cti():

    return {

        "plataforma": "CTI — Commercial Tactical Intelligence",

        "versao": "2.0",

        "modulos": [

            "mercado_anfir",
            "clientes",
            "equipamentos",
            "implementadores",
            "vendas",
            "pipeline",
            "contatos",
            "analytics",
            "radar_territorial"

        ]

    }

# ============================================================
# CONTROLE DE PERÍODO ANFIR (EVITAR DUPLICAÇÃO)
# ============================================================

from datetime import datetime

def limpar_periodo_anfir(ano, mes):

    try:

        supabase.table("cti_anfir") \
        .delete() \
        .eq("ano", ano) \
        .eq("mes", mes) \
        .execute()

        print(f"[ANFIR] registros antigos removidos {mes}/{ano}")

    except Exception as e:

        print(f"[ANFIR] erro ao limpar período: {str(e)}")

def processar_anfir_mensal(contents, ano):

    df = pd.read_excel(io.BytesIO(contents))
    df = df.fillna("")

    # normalizar nomes das colunas
    df.columns = [normalizar_texto(c) for c in df.columns]

    registros = []

    meses_validos = [
        "JANEIRO","FEVEREIRO","MARCO","MARÇO",
        "ABRIL","MAIO","JUNHO","JULHO",
        "AGOSTO","SETEMBRO","OUTUBRO",
        "NOVEMBRO","DEZEMBRO"
    ]

    for _, row in df.iterrows():

        for col in df.columns:

            if col not in meses_validos:
                continue

            valor = row.get(col)

            try:
                valor_num = float(valor)
            except:
                valor_num = 0

            if valor_num <= 0:
                continue

            registro = {
                "ano": ano,
                "mes": col,
                "estado": normalizar_texto(row.get("ESTADO")),
                "linha": normalizar_texto(
                    row.get("LINHA") or 
                    row.get("PRODUTO") or 
                    row.get("TIPO")
                ),
                "implementador": normalizar_texto(
                    row.get("IMPLEMENTADOR") or 
                    row.get("OEM") or 
                    row.get("FABRICANTE")
                ),
                "valor": valor_num
            }

            registros.append(registro)

    return registros

# ============================================================
# UPLOAD ANFIR COM CONTROLE DE MÊS
# ============================================================

@app.post("/upload/anfir/seguro")
async def upload_anfir_seguro(file: UploadFile = File(...)):

    try:

        contents = await file.read()

        registros = processar_anfir_mensal(contents, datetime.now().year)

        registros_processados = []

        mapa_meses = {
            "JANEIRO": 1,
            "FEVEREIRO": 2,
            "MARCO": 3,
            "MARÇO": 3,
            "ABRIL": 4,
            "MAIO": 5,
            "JUNHO": 6,
            "JULHO": 7,
            "AGOSTO": 8,
            "SETEMBRO": 9,
            "OUTUBRO": 10,
            "NOVEMBRO": 11,
            "DEZEMBRO": 12
        }

        for r in registros:

            mes_texto = normalizar_texto(
                r.get("mes") or 
                r.get("MÊS") or 
                r.get("MES")
            )

            mes_num = mapa_meses.get(mes_texto)
            ano = datetime.now().year

            # 🔥 NÃO BLOQUEIA MAIS REGISTRO SEM MÊS
            if not mes_num:
                mes_num = 0

            registros_processados.append({
                "ano": ano,
                "mes": mes_num,
                "estado": r.get("estado"),
                "linha": r.get("linha"),
                "implementador": r.get("implementador"),
                "valor": float(r.get("valor", 0))
            })

        # =========================
        # VALIDAÇÃO PRÉ-INSERT
        # =========================

        if not registros_processados:
            raise Exception("ERRO: nenhum registro processado")

        # =========================
        # INSERT CONTROLADO
        # =========================

        total_inserido = 0
        batch_size = 500

        for i in range(0, len(registros_processados), batch_size):

            batch = registros_processados[i:i + batch_size]

            response = supabase.table("cti_anfir").insert(batch).execute()

            if response.data:
                total_inserido += len(response.data)

        # =========================
        # VALIDAÇÃO PÓS-INSERT
        # =========================

        if total_inserido == 0:
            raise Exception("ERRO CRÍTICO: insert não gravou nada")

        count_check = supabase.table("cti_anfir").select("*", count="exact").execute()

        if count_check.count == 0:
            raise Exception("ERRO CRÍTICO: tabela continua vazia")

        return {
            "status": "ANFIR carregado com sucesso",
            "processados": len(registros_processados),
            "inseridos": total_inserido,
            "total_tabela": count_check.count
        }

    except Exception as e:

        print("ERRO UPLOAD ANFIR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar planilha: {str(e)}"
        )
        
# ============================================================
# LOG DE UPLOAD ANFIR
# ============================================================

def registrar_log_upload_anfir(ano, mes, total):

    try:

        supabase.table("anfir_upload_logs").insert({

            "data_upload": datetime.now().isoformat(),
            "ano": ano,
            "mes": mes,
            "linhas_importadas": total

        }).execute()

    except Exception as e:

        print(f"[ANFIR LOG] erro: {str(e)}")

# ============================================================
# EXPORTAÇÃO DE RELATÓRIO PDF
# ============================================================

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from fastapi.responses import FileResponse
import uuid
import os

@app.get("/analytics/export-pdf")
def exportar_relatorio_pdf():

    vendas = supabase.table("vendas").select("*").execute()

    total_vendas = len(vendas.data)

    faturamento_total = 0

    for v in vendas.data:

        valor = v.get("valor")

        try:

            faturamento_total += float(valor)

        except:

            pass

    filename = f"/tmp/cti_report_{uuid.uuid4()}.pdf"

    c = canvas.Canvas(filename, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(80, 800, "CTI — Commercial Tactical Intelligence")

    c.setFont("Helvetica", 12)

    c.drawString(80, 760, f"Total de vendas registradas: {total_vendas}")
    c.drawString(80, 740, f"Faturamento total: R$ {round(faturamento_total,2)}")

    c.drawString(80, 700, "Relatório gerado automaticamente pelo sistema CTI")

    c.drawString(80, 680, f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c.save()

    return FileResponse(

        filename,
        media_type="application/pdf",
        filename="cti_relatorio.pdf"

    )

# ==========================================================
# ENDPOINT — PERÍODOS DISPONÍVEIS
# ==========================================================

@app.get("/analytics/periodos-disponiveis")
def periodos_disponiveis():

    try:

        response = supabase.table("cti_anfir")\
            .select("ano, mes")\
            .execute()

        dados = response.data

        periodos = sorted(
            {(d["ano"], d["mes"]) for d in dados},
            reverse=True
        )

        lista = [
            {"ano": p[0], "mes": p[1]}
            for p in periodos
        ]

        return {"periodos": lista}

    except Exception as e:

        return {
            "erro": "falha ao buscar períodos",
            "detalhe": str(e)
        }

# ==========================================================
# ENDPOINT — INTELIGÊNCIA COMERCIAL COM FILTRO
# ==========================================================

@app.get("/analytics/inteligencia-comercial")
def inteligencia_comercial(ano: int = None, mes: int = None):

    try:

        query = supabase.table("cti_anfir").select("*")

        if ano:
            query = query.eq("ano", ano)

        if mes:
            query = query.eq("mes", mes)

        response = query.execute()

        dados = response.data

        if not dados:
            return {"mensagem": "sem dados para período"}

        df = pd.DataFrame(dados)

        resumo = {
            "total_vendas": int(df["valor"].sum()),
            "total_registros": len(df)
        }

        performance_estado = (
            df.groupby("estado")["valor"]
            .sum()
            .reset_index()
            .to_dict(orient="records")
        )

        performance_linha = (
            df.groupby("linha")["valor"]
            .sum()
            .reset_index()
            .to_dict(orient="records")
        )

        ranking_oem = (
            df.groupby("implementador")["valor"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .to_dict(orient="records")
        )

        return {

            "filtro": {
                "ano": ano,
                "mes": mes
            },

            "resumo_geral": resumo,
            "performance_por_estado": performance_estado,
            "performance_por_linha": performance_linha,
            "ranking_oem": ranking_oem

        }

    except Exception as e:

        return {
            "erro": "falha na análise",
            "detalhe": str(e)
        }

# ==========================================================
# ENGINE CTI — MARKET INTELLIGENCE
# ==========================================================

@app.get("/engine/market-intelligence")
def market_intelligence():

    vendas = select_all("cti_anfir")

    engine = MarketEngine(vendas)

    return {

        "regional_analysis": engine.regional_analysis(),

        "oem_share": engine.oem_share(),

        "product_lines": engine.product_lines(),

        "underperforming_regions": engine.underperforming_regions(),

        "market_dominance": engine.market_dominance()

    }

@app.get("/engine/test-db")
def test_db():
    data = supabase.table("cti_anfir").select("*").limit(5).execute()
    return data.data

# ==========================================================
# WIN / LOSS ANALYSIS
# ==========================================================

@app.get("/analytics/win-loss")
def win_loss():

    anf_ir = supabase.table("cti_anfir").select("*").execute().data
    negociacoes = supabase.table("negociacoes").select("*").execute().data

    engine = WinLossEngine(anf_ir, negociacoes)

    return {
        "win_loss": engine.calcular_win_loss(),
        "insights": engine.insights()
    }

@app.get("/analytics/win-loss-intelligence")
def win_loss_intelligence():

    anf_ir = supabase.table("cti_anfir").select("*").execute().data
    negociacoes = supabase.table("negociacoes").select("*").execute().data

    engine = WinLossEngine(anf_ir, negociacoes)

    return {
        "win_loss": engine.calcular_win_loss(),
        "insights": engine.insights(),
        "analise_perdas": engine.analise_perdas()
    }

@app.get("/analytics/win-loss-recomendacoes")
def win_loss_recomendacoes():

    anf_ir = supabase.table("cti_anfir").select("*").execute().data
    negociacoes = supabase.table("negociacoes").select("*").execute().data

    engine = WinLossEngine(anf_ir, negociacoes)

    return {
        "recomendacoes": engine.recomendacoes()
    }

# ============================================================
# CTI V3 — CAMADA INTELIGENTE (SEM IMPACTO NO SISTEMA ATUAL)
# ============================================================

DDD_VIENA = ["011", "012", "013", "014", "015", "018"]

def obter_ddd_safe(cidade):

    try:
        cidade = normalizar_texto(cidade)

        response = supabase.table("cidades_ddd")\
            .select("ddd")\
            .ilike("cidade", f"%{cidade}%")\
            .execute()

        if response.data:
            return response.data[0]["ddd"]

    except:
        pass

    return None


def normalizar_cnpj(cnpj):

    if not cnpj:
        return None

    return re.sub(r"\D", "", str(cnpj))


def indexar_por_cnpj(lista):

    mapa = {}

    for item in lista:

        cnpj = normalizar_cnpj(item.get("cnpj"))

        if not cnpj:
            continue

        mapa[cnpj] = item

    return mapa


@app.get("/cti/v3/win-loss-real")
def cti_win_loss_real():

    anf_ir = select_all("cti_anfir")
    negociacoes = select_all("negociacoes")

    anf_map = indexar_por_cnpj(anf_ir)
    neg_map = indexar_por_cnpj(negociacoes)

    ganhos = []
    perdas = []
    fora_area = []

    for cnpj, venda in anf_map.items():

        cidade = venda.get("cidade")
        ddd = venda.get("ddd") or obter_ddd_safe(cidade)

        if ddd not in DDD_VIENA:
            fora_area.append(venda)
            continue

        if cnpj in neg_map:
            ganhos.append(venda)
        else:
            perdas.append(venda)

    return {
        "ganhos": len(ganhos),
        "perdas": len(perdas),
        "fora_area": len(fora_area)
    }


@app.get("/cti/v3/perdas-detalhadas")
def cti_perdas_detalhadas():

    anf_ir = select_all("cti_anfir")
    negociacoes = select_all("negociacoes")

    anf_map = indexar_por_cnpj(anf_ir)
    neg_map = indexar_por_cnpj(negociacoes)

    perdas = []

    for cnpj, venda in anf_map.items():

        cidade = venda.get("cidade")
        ddd = venda.get("ddd") or obter_ddd_safe(cidade)

        if ddd not in DDD_VIENA:
            continue

        if cnpj not in neg_map:

            perdas.append({
                "cliente": venda.get("cliente"),
                "cidade": cidade,
                "ddd": ddd,
                "valor": venda.get("valor"),
                "implementador": venda.get("implementador")
            })

    return perdas[:100]


@app.get("/cti/v3/oportunidades")
def cti_oportunidades():

    perdas = cti_perdas_detalhadas()

    oportunidades = []

    for p in perdas:

        oportunidades.append({
            "cliente": p["cliente"],
            "acao": "Atuar imediatamente",
            "regiao": p["cidade"],
            "ddd": p["ddd"]
        })

    return oportunidades[:50]

# ============================================================
# CTI CORE — CONSOLIDAÇÃO REAL DE DADOS
# ============================================================

def resolver_cnpj_unificado(registro):

    # prioridade: CNPJ direto
    if registro.get("cnpj"):
        return re.sub(r"\D", "", str(registro.get("cnpj")))

    # placa
    if registro.get("placa"):
        veiculo = resolver_cliente_por_placa(registro.get("placa"))
        if veiculo:
            return veiculo.get("cnpj")

    # nome
    if registro.get("cliente"):
        cliente = resolver_cliente_por_nome(registro.get("cliente"))
        if cliente:
            return cliente.get("cnpj")

    return None


def obter_ddd_unificado(cidade):

    try:
        cidade = normalizar_texto(cidade)

        response = supabase.table("cidades_ddd")\
            .select("ddd")\
            .ilike("cidade", f"%{cidade}%")\
            .execute()

        if response.data:
            return response.data[0]["ddd"]

    except:
        pass

    return None


@app.get("/cti/core/consolidar")
def cti_consolidar():

    anf_ir = select_all("cti_anfir")
    negociacoes = select_all("negociacoes")
    pipeline = select_all("pipeline")

    base_final = []

    # ========================================================
    # ANFIR → MERCADO (RESULTADO)
    # ========================================================

    for r in anf_ir:

        cnpj = resolver_cnpj_unificado(r)

        base_final.append({
            "cliente": r.get("cliente"),
            "cnpj": cnpj,
            "cidade": r.get("cidade"),
            "ddd": obter_ddd_unificado(r.get("cidade")),
            "origem": "ANFIR",
            "status": "REALIZADO",
            "valor": r.get("valor")
        })

    # ========================================================
    # NEGOCIAÇÕES → TENTATIVA
    # ========================================================

    for n in negociacoes:

        cnpj = resolver_cnpj_unificado(n)

        base_final.append({
            "cliente": n.get("cliente"),
            "cnpj": cnpj,
            "cidade": n.get("cidade"),
            "ddd": obter_ddd_unificado(n.get("cidade")),
            "origem": "NEGOCIACAO",
            "status": normalizar_texto(n.get("status")),
            "valor": n.get("valor")
        })

    # ========================================================
    # PIPELINE → INTENÇÃO
    # ========================================================

    for p in pipeline:

        cnpj = resolver_cnpj_unificado(p)

        base_final.append({
            "cliente": p.get("cliente"),
            "cnpj": cnpj,
            "cidade": p.get("cidade"),
            "ddd": obter_ddd_unificado(p.get("cidade")),
            "origem": "FUNIL",
            "status": "INTENCAO",
            "valor": p.get("valor")
        })

    return {
        "total_registros": len(base_final),
        "amostra": base_final[:50]
    }

# ============================================================
# UPLOAD CONTATOS
# ============================================================

@app.post("/upload/contatos")
async def upload_contatos(file: UploadFile = File(...)):

    contents = await file.read()

    df = pd.read_excel(io.BytesIO(contents))
    df = df.fillna("")

    df.columns = [str(c).strip().upper() for c in df.columns]

    registros = []

    for _, row in df.iterrows():

        cliente = normalizar_texto(row.get("CLIENTE"))
        cnpj = re.sub(r"\D", "", str(row.get("CNPJ")))

        if not cliente:
            continue

        registros.append({
            "cliente": cliente,
            "cnpj": cnpj
        })

    if not registros:
        return {"status": "sem dados"}

    batch_size = 500

    for i in range(0, len(registros), batch_size):

        batch = registros[i:i + batch_size]

        supabase.table("contatos").insert(batch).execute()

    return {
        "status": "contatos carregados",
        "registros": len(registros)
    }

# ============================================================
# UPLOAD FUNIL
# ============================================================

@app.post("/upload/funil")
async def upload_funil(file: UploadFile = File(...)):

    contents = await file.read()

    df = pd.read_excel(io.BytesIO(contents))
    df = df.fillna("")

    df.columns = [str(c).strip().upper() for c in df.columns]

    registros = []

    for _, row in df.iterrows():

        cliente = normalizar_texto(row.get("CLIENTE"))
        valor = limpar_valor(row.get("VALOR"))
        data = row.get("DATA")
        representante = normalizar_texto(row.get("REPRESENTANTE"))

        if not cliente:
            continue

        registros.append({
            "cliente": cliente,
            "valor": valor,
            "data": data,
            "representante": representante
        })

    if not registros:
        return {"status": "sem dados"}

    batch_size = 500

    for i in range(0, len(registros), batch_size):

        batch = registros[i:i + batch_size]

        supabase.table("funil").insert(batch).execute()

    return {
        "status": "funil carregado",
        "registros": len(registros)
    }

# ============================================================
# UPLOAD NEGOCIACOES
# ============================================================

@app.post("/upload/negociacoes")
async def upload_negociacoes(file: UploadFile = File(...)):

    try:
        contents = await file.read()

        df = pd.read_excel(io.BytesIO(contents))
        df = df.fillna("")

        # normaliza colunas (padronização total)
        df.columns = [str(c).strip().upper() for c in df.columns]

        registros = []

        for _, row in df.iterrows():

            try:
                # =========================
                # EXTRAÇÃO FLEXÍVEL (AGRESSIVA)
                # =========================

                cliente = normalizar_texto(
                    row.get("CLIENTE")
                    or row.get("CLIENTE FINAL")
                    or row.get("RAZAO SOCIAL")
                    or ""
                )

                valor = limpar_valor(
                    row.get("VALOR")
                    or row.get("TOTAL")
                    or row.get("VALOR TOTAL")
                    or 0
                )

                vendedor = normalizar_texto(
                    row.get("VENDEDOR")
                    or row.get("CONSULTOR")
                    or row.get("REPRESENTANTE")
                    or ""
                )

                data = (
                    row.get("DATA")
                    or row.get("DATA VENDA")
                    or row.get("FECHAMENTO")
                    or None
                )

                condicao = (
                    row.get("CONDICAO_COMERCIAL")
                    or row.get("CONDICAO")
                    or row.get("FORMA PAGAMENTO")
                    or ""
                )

                # =========================
                # REGRA MÍNIMA
                # =========================

                if not cliente and not valor:
                    continue

                registros.append({
                    "cliente": cliente,
                    "valor": float(valor or 0),
                    "vendedor": vendedor,
                    "data": data,
                    "condicao_comercial": condicao
                })

            except Exception as e:
                print("[NEGOCIACOES ERRO REGISTRO]", str(e))
                continue

        if not registros:
            return {
                "status": "erro",
                "mensagem": "nenhum registro válido encontrado"
            }

        # =========================
        # INSERT CONTROLADO
        # =========================

        total_inserido = 0
        batch_size = 500

        for i in range(0, len(registros), batch_size):

            batch = registros[i:i + batch_size]

            response = supabase.table("negociacoes").insert(batch).execute()

            if response.data:
                total_inserido += len(response.data)
            else:
                print("[ERRO INSERT NEGOCIACOES]")

        total_tabela = supabase.table("negociacoes") \
            .select("*", count="exact") \
            .execute().count

        return {
            "status": "NEGOCIACOES processado 100%",
            "extraidos": len(registros),
            "inseridos": total_inserido,
            "total_base": total_tabela
        }

    except Exception as e:

        print("[ERRO NEGOCIACOES GLOBAL]", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ============================================================
# CTI PROCESSADOR (CNPJ + CONSOLIDAÇÃO INICIAL)
# ============================================================

@app.post("/cti/processar")
def processar_cti():

    anfirs = select_all("cti_anfir")
    negociacoes = select_all("negociacoes")
    funil = select_all("funil")
    contatos = select_all("contatos")
    cidades = select_all("cidades_ddd")

    mapa_cidade = gerar_mapa_cidade()

    # MAPA CNPJ
    mapa_cnpj = {}
    for c in contatos:
        cliente = normalizar_texto(c.get("cliente"))
        cnpj = re.sub(r"\D", "", str(c.get("cnpj")))
        if cliente:
            mapa_cnpj[cliente] = cnpj

    # MAPA DDD
    mapa_ddd = {}
    for c in cidades:
        cidade = normalizar_texto(c.get("cidade"))
        mapa_ddd[cidade] = str(c.get("ddd"))

    base = []

    # =========================
    # ANFIR
    # =========================
    for r in anfirs:

        cliente = normalizar_chave(r.get("cliente"))

        if not cliente:
            continue
            
        cidade = normalizar_chave(r.get("cidade"))
        cidade = enriquecer_cidade(cliente, cidade, mapa_cidade)

        base.append({
            "data": r.get("data_venda"),
            "cliente": cliente,
            "cnpj": mapa_cnpj.get(cliente),
            "cidade": cidade,
            "uf": r.get("estado"),
            "ddd": mapa_ddd.get(cidade),
            "valor": 0,
            "condicao_comercial": None,
            "oem": r.get("implementador"),
            "locadora": None,
            "vendedor": None,
            "tipo_venda": "indireta_oem" if r.get("implementador") else "direta",
            "marca_caminhao": None,
            "modelo_caminhao": None
        })

    # =========================
    # NEGOCIAÇÕES
    # =========================
    for r in negociacoes:

        cliente = normalizar_chave(r.get("cliente"))

        if not cliente:
            continue
            
        cidade = enriquecer_cidade(cliente, None, mapa_cidade)

        base.append({
            "data": r.get("data"),
            "cliente": cliente,
            "cnpj": mapa_cnpj.get(cliente),
            "cidade": cidade,
            "uf": None,
            "ddd": None,
            "valor": limpar_valor(r.get("valor")),
            "condicao_comercial": r.get("condicao_comercial"),
            "oem": None,
            "locadora": None,
            "vendedor": r.get("vendedor"),
            "tipo_venda": "direta",
            "marca_caminhao": None,
            "modelo_caminhao": None
        })

    # =========================
    # FUNIL
    # =========================
    for r in funil:

        cliente = normalizar_chave(r.get("cliente"))

        if not cliente:
            continue
        
        cidade = enriquecer_cidade(cliente, None, mapa_cidade)

        base.append({
            "data": r.get("data"),
            "cliente": cliente,
            "cnpj": mapa_cnpj.get(cliente),
            "cidade": cidade,
            "uf": None,
            "ddd": None,
            "valor": limpar_valor(r.get("valor")),
            "condicao_comercial": None,
            "oem": None,
            "locadora": None,
            "vendedor": r.get("representante"),
            "tipo_venda": "direta",
            "marca_caminhao": None,
            "modelo_caminhao": None
        })

    # LIMPAR BASE ANTIGA
    supabase.table("cti_unificado").delete().gt("created_at", "1900-01-01").execute()

    # INSERIR NOVA BASE
    batch_size = 500

    for i in range(0, len(base), batch_size):

        batch = base[i:i + batch_size]

        supabase.table("cti_unificado").insert(batch).execute()

    return {
        "status": "cti consolidado",
        "registros": len(base)
    }

# ============================================================
# NORMALIZAÇÃO AVANÇADA
# ============================================================

def normalizar_chave(texto):
    if not texto:
        return ""

    texto = normalizar_texto(texto)

    substituicoes = {
        " LTDA": "",
        " EIRELI": "",
        " SA": "",
        " S/A": "",
        " ME": "",
        " EPP": ""
    }

    for k, v in substituicoes.items():
        texto = texto.replace(k, v)

    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

# ============================================================
# VALIDAR DDD
# ============================================================

@app.get("/cti/validar-ddd")
def validar_ddd():

    dados = select_all("cti_unificado")

    total = len(dados)
    com_ddd = 0
    sem_ddd = 0

    exemplos_sem_ddd = []

    for r in dados:

        if r.get("ddd"):
            com_ddd += 1
        else:
            sem_ddd += 1

            if len(exemplos_sem_ddd) < 10:
                exemplos_sem_ddd.append({
                    "cliente": r.get("cliente"),
                    "cidade": r.get("cidade")
                })

    percentual = (com_ddd / total * 100) if total > 0 else 0

    return {
        "total": total,
        "com_ddd": com_ddd,
        "sem_ddd": sem_ddd,
        "percentual_cobertura": round(percentual, 2),
        "exemplos_sem_ddd": exemplos_sem_ddd
    }

def enriquecer_cidade(cliente, cidade, mapa_cidade):

    if cidade:
        return cidade

    if cliente and cliente in mapa_cidade:
        return mapa_cidade.get(cliente)

    return None

def gerar_mapa_cidade():
    mapa = {}
    anfirs = select_all("cti_anfir")

    for r in anfirs:
        cliente = normalizar_texto(r.get("cliente"))
        cidade = normalizar_texto(r.get("cidade"))

        if cliente and cidade:
            mapa[cliente] = cidade

    return mapa

@app.post("/cti/reset")
def reset_cti():

    try:

        response = supabase.table("cti_anfir").delete().execute()

        return {
            "status": "reset concluído",
            "registros_removidos": len(response.data) if response.data else 0
        }

    except Exception as e:

        return {
            "status": "erro",
            "mensagem": str(e)
        }

# ============================================================
# DEBUG INTELIGENTE ANFIR (NÃO AFETA SISTEMA ATUAL)
# ============================================================

@app.post("/debug/anfir")
async def debug_anfir(file: UploadFile = File(...)):

    contents = await file.read()

    df = pd.read_excel(io.BytesIO(contents))
    df = df.fillna("")

    colunas = list(df.columns)

    total_linhas = len(df)

    # tenta identificar colunas numéricas automaticamente
    colunas_numericas = []

    for col in df.columns:
        try:
            if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0:
                colunas_numericas.append(col)
        except:
            continue

    amostra = df.head(5).to_dict(orient="records")

    return {
        "total_linhas": total_linhas,
        "colunas": colunas,
        "colunas_numericas_detectadas": colunas_numericas,
        "amostra_dados": amostra
    }

# ============================================================
# ANFIR ENGINE 100% INTELIGENTE (SEMÂNTICA + ESTRUTURA + ANTI-DUPLICAÇÃO)
# ============================================================

import unicodedata
import re
import pandas as pd
import io
import hashlib

def limpar_texto(txt):
    if not txt:
        return ""

    txt = str(txt).lower()
    txt = unicodedata.normalize('NFKD', txt)
    txt = txt.encode('ASCII', 'ignore').decode('ASCII')
    txt = re.sub(r'[^a-z0-9 ]', '', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()

    return txt


MAPA_COLUNAS = {
    "mes": ["mes", "mês", "periodo", "competencia"],
    "estado": ["estado", "uf"],
    "municipio": ["municipio", "cidade"],
    "fabricante": ["fabricante", "fornecedor"],
    "cliente": ["cliente final", "cliente"],
    "segmento": ["segmento", "linha"],
    "valor": ["total", "valor", "qtd", "quantidade"]
}


def identificar_coluna(coluna):
    col = limpar_texto(coluna)

    for chave, variacoes in MAPA_COLUNAS.items():
        for termo in variacoes:
            if termo in col:
                return chave

    return None


def extrair_numero(row):
    for val in row:
        try:
            num = float(str(val).replace(",", "."))
            if num > 0:
                return num
        except:
            continue
    return 0


def hash_registro(reg):
    chave = f"{reg['mes']}_{reg['estado']}_{reg['municipio']}_{reg['fabricante']}_{reg['valor']}"
    return hashlib.md5(chave.encode()).hexdigest()


def normalizar_anfir_100(contents):

    import pandas as pd
    import io
    import re
    from datetime import datetime

    def limpar(txt):
        if txt is None:
            return ""
        return str(txt).strip()

    def detectar_mes(txt):
        mapa = {
            "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3,
            "abril": 4, "maio": 5, "junho": 6, "julho": 7,
            "agosto": 8, "setembro": 9, "outubro": 10,
            "novembro": 11, "dezembro": 12
        }
        txt = str(txt).lower()
        for k, v in mapa.items():
            if k in txt:
                return v
        return None

    def detectar_ano(txt):
        match = re.search(r'20\d{2}', str(txt))
        if match:
            return int(match.group())
        return None

    registros = []

    xls = pd.ExcelFile(io.BytesIO(contents))

    for aba in xls.sheet_names:

        df = xls.parse(aba, header=None)
        df = df.fillna("")

        contexto_mes = detectar_mes(aba)
        contexto_ano = detectar_ano(aba) or datetime.now().year

        for i in range(len(df)):

            linha = df.iloc[i].tolist()

            valor = None
            cidade = None
            cliente = None
            implementador = None
            linha_tipo = None
            estado = None

            for celula in linha:

                txt = limpar(celula)

                # valor (regra principal)
                try:
                    v = float(str(txt).replace(",", "."))
                    if v > 0:
                        valor = v
                except:
                    pass

                # cidade (texto puro maior)
                if not cidade and txt.isalpha() and len(txt) > 3:
                    cidade = txt.upper()

                # cliente (texto longo)
                if not cliente and len(txt) > 10:
                    cliente = txt

                # implementador (palavras comuns OEM)
                if not implementador and len(txt) > 3 and len(txt) < 20:
                    implementador = txt

                # segmento
                if not linha_tipo and any(x in txt.lower() for x in ["truck", "trailer", "drive"]):
                    linha_tipo = txt

                # estado simples
                if txt.upper() in ["SP","MG","PR","SC","RS","BA","GO","MT","MS","RJ","DF"]:
                    estado = txt.upper()

            # 🔥 REGRA AGRESSIVA
            if not valor:
                continue

            registro = {
                "ano": contexto_ano,
                "mes": contexto_mes or 0,
                "estado": estado,
                "cidade": cidade,
                "cliente": cliente,
                "implementador": implementador,
                "linha": linha_tipo,
                "valor": valor
            }

            registros.append(registro)

    return registros

# ============================================================
# CTI — INTELIGÊNCIA AVANÇADA POR PERÍODO (NÃO CUMULATIVA)
# ============================================================

@app.get("/analytics/inteligencia-periodo")
def inteligencia_periodo(ano: int = None, mes: int = None):

    try:

        query = supabase.table("cti_anfir").select("*")

        if ano:
            query = query.eq("ano", ano)

        if mes:
            query = query.eq("mes", mes)

        response = query.execute()
        dados = response.data

        if not dados:
            return {"mensagem": "sem dados para o período informado"}

        df = pd.DataFrame(dados)

        # ====================================================
        # BASE DO PERÍODO (SEM ACUMULAR)
        # ====================================================

        total_valor = df["valor"].sum()
        total_registros = len(df)

        # ====================================================
        # AGRUPAMENTOS
        # ====================================================

        estado = df.groupby("estado")["valor"].sum().reset_index()
        linha = df.groupby("linha")["valor"].sum().reset_index()
        oem = df.groupby("implementador")["valor"].sum().reset_index()

        # ====================================================
        # RANKINGS
        # ====================================================

        top_estados = estado.sort_values(by="valor", ascending=False).head(5)
        top_linhas = linha.sort_values(by="valor", ascending=False).head(5)
        top_oem = oem.sort_values(by="valor", ascending=False).head(5)

        # ====================================================
        # PARTICIPAÇÃO DE MERCADO (SHARE)
        # ====================================================

        estado["share"] = (estado["valor"] / total_valor * 100).round(2)
        linha["share"] = (linha["valor"] / total_valor * 100).round(2)
        oem["share"] = (oem["valor"] / total_valor * 100).round(2)

        # ====================================================
        # OPORTUNIDADES (INTELIGENTES)
        # ====================================================

        oportunidades = []

        for _, row in estado.iterrows():
            if row["valor"] < (total_valor * 0.05):
                oportunidades.append({
                    "tipo": "estado_oportunidade",
                    "estado": row["estado"],
                    "motivo": "baixo share no período"
                })

        for _, row in linha.iterrows():
            if row["valor"] < (total_valor * 0.05):
                oportunidades.append({
                    "tipo": "linha_oportunidade",
                    "linha": row["linha"],
                    "motivo": "baixa penetração"
                })

        # ====================================================
        # RESULTADO FINAL
        # ====================================================

        return {

            "periodo": {
                "ano": ano,
                "mes": mes
            },

            "resumo": {
                "total_valor": float(total_valor),
                "total_registros": int(total_registros)
            },

            "top_estados": top_estados.to_dict(orient="records"),
            "top_linhas": top_linhas.to_dict(orient="records"),
            "top_oem": top_oem.to_dict(orient="records"),

            "share_por_estado": estado.to_dict(orient="records"),
            "share_por_linha": linha.to_dict(orient="records"),
            "share_por_oem": oem.to_dict(orient="records"),

            "oportunidades": oportunidades

        }

    except Exception as e:

        return {
            "erro": "falha na inteligência por período",
            "detalhe": str(e)
        }


# ============================================================
# COMPARAÇÃO ENTRE PERÍODOS (EVOLUÇÃO REAL)
# ============================================================

@app.get("/analytics/comparativo-periodo")
def comparativo_periodo(ano1: int, ano2: int):

    try:

        df1 = pd.DataFrame(
            supabase.table("cti_anfir").select("*").eq("ano", ano1).execute().data
        )

        df2 = pd.DataFrame(
            supabase.table("cti_anfir").select("*").eq("ano", ano2).execute().data
        )

        if df1.empty or df2.empty:
            return {"mensagem": "dados insuficientes para comparação"}

        total1 = df1["valor"].sum()
        total2 = df2["valor"].sum()

        crescimento = ((total2 - total1) / total1 * 100) if total1 > 0 else 0

        return {

            "comparacao": {
                "ano_1": ano1,
                "ano_2": ano2,
                "valor_ano_1": float(total1),
                "valor_ano_2": float(total2),
                "crescimento_percentual": round(crescimento, 2)
            }

        }

    except Exception as e:

        return {
            "erro": "falha na comparação",
            "detalhe": str(e)
        }

# ============================================================
# ANFIR ENGINE DEFINITIVO (SUBSTITUI TODOS OS OUTROS)
# ============================================================

@app.post("/upload/anfir/full")
async def upload_anfir_full(file: UploadFile = File(...)):

    try:

        contents = await file.read()

        registros = normalizar_anfir_100(contents)

        if not registros:
            return {
                "status": "erro",
                "mensagem": "nenhum registro extraído da planilha"
            }

        mapa_meses = {
            "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3,
            "abril": 4, "maio": 5, "junho": 6, "julho": 7,
            "agosto": 8, "setembro": 9, "outubro": 10,
            "novembro": 11, "dezembro": 12
        }

        registros_final = []

        for r in registros:

            try:

                mes_txt = limpar_texto(r.get("mes"))
                mes_num = mapa_meses.get(mes_txt, 0)

                ano = r.get("ano") or datetime.now().year

                registros_final.append({
                    "ano": ano,
                    "mes": mes_num,
                    "estado": normalizar_texto(r.get("estado")),
                    "cidade": normalizar_texto(r.get("municipio")),
                    "linha": normalizar_texto(r.get("segmento")),
                    "implementador": normalizar_texto(r.get("fabricante")),
                    "cliente": normalizar_texto(r.get("cliente")),
                    "valor": float(r.get("valor", 0))
                })

            except Exception as e:
                print("[ANFIR ERRO REGISTRO]", str(e))
                continue

        total_inserido = 0
        batch_size = 500

        for i in range(0, len(registros_final), batch_size):

            batch = registros_final[i:i + batch_size]

            response = supabase.table("cti_anfir").insert(batch).execute()

            if response.data:
                total_inserido += len(response.data)

        if total_inserido == 0:
            raise Exception("Falha ao inserir dados")

        total_tabela = supabase.table("cti_anfir")\
            .select("*", count="exact")\
            .execute().count

        return {
            "status": "ANFIR processado 100%",
            "extraidos": len(registros),
            "inseridos": total_inserido,
            "total_base": total_tabela
        }

    except Exception as e:

        print("ERRO REAL:", str(e))

        return {
            "status": "erro",
            "mensagem": str(e)
        }

# ============================================================
# CTI CORE V4 — CONSOLIDADOR UNIVERSAL + TEMPO INTELIGENTE
# ============================================================

import unicodedata
import hashlib

# ============================================================
# NORMALIZAÇÃO FORTE
# ============================================================

def normalizar_texto_forte(txt):
    if not txt:
        return ""

    txt = str(txt).upper().strip()
    txt = unicodedata.normalize('NFKD', txt)
    txt = txt.encode('ASCII', 'ignore').decode('ASCII')
    txt = re.sub(r'[^A-Z0-9 ]', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt)

    return txt.strip()


# ============================================================
# NÚMERO INTELIGENTE
# ============================================================

def extrair_numero_inteligente(valor):
    try:
        if valor is None:
            return 0

        txt = str(valor).replace(".", "").replace(",", ".")
        num = float(txt)

        if num > 0:
            return num
    except:
        pass

    return 0


# ============================================================
# DETECÇÃO DE IDENTIDADE
# ============================================================

def detectar_tipo_dado(valor):

    if not valor:
        return None

    texto = str(valor)
    numeros = re.sub(r"\D", "", texto)

    if len(numeros) == 14:
        return ("CNPJ", numeros)

    if len(texto) >= 7 and any(c.isalpha() for c in texto):
        return ("PLACA", normalizar_texto_forte(texto))

    if len(texto) > 3:
        return ("NOME", normalizar_texto_forte(texto))

    return None


# ============================================================
# MAPA DE MESES UNIVERSAL
# ============================================================

MAPA_MESES = {
    "JAN": 1, "JANEIRO": 1,
    "FEV": 2, "FEVEREIRO": 2,
    "MAR": 3, "MARCO": 3, "MARÇO": 3,
    "ABR": 4, "ABRIL": 4,
    "MAI": 5, "MAIO": 5,
    "JUN": 6, "JUNHO": 6,
    "JUL": 7, "JULHO": 7,
    "AGO": 8, "AGOSTO": 8,
    "SET": 9, "SETEMBRO": 9,
    "OUT": 10, "OUTUBRO": 10,
    "NOV": 11, "NOVEMBRO": 11,
    "DEZ": 12, "DEZEMBRO": 12
}


# ============================================================
# DETECÇÃO DE TEMPO EM QUALQUER LUGAR
# ============================================================

def detectar_tempo_em_texto(texto):

    texto = normalizar_texto_forte(texto)

    ano = None
    mes = None

    # ANO
    match_ano = re.search(r"(20\d{2})", texto)
    if match_ano:
        ano = int(match_ano.group(1))

    # MÊS
    for k in MAPA_MESES:
        if k in texto:
            mes = MAPA_MESES[k]
            break

    return ano, mes


# ============================================================
# LEITOR UNIVERSAL MULTI-ABAS
# ============================================================

def ler_planilha_inteligente_v4(contents):

    xls = pd.ExcelFile(io.BytesIO(contents))
    registros = []

    ano_global = None
    mes_global = None

    # =========================
    # DETECTA TEMPO NO NOME DAS ABAS
    # =========================

    for aba in xls.sheet_names:
        a, m = detectar_tempo_em_texto(aba)

        if a:
            ano_global = a
        if m:
            mes_global = m

    # =========================
    # PROCESSA TODAS AS ABAS
    # =========================

    for aba in xls.sheet_names:

        df = pd.read_excel(xls, sheet_name=aba, header=None)
        df = df.fillna("")

        for _, row in df.iterrows():

            linha = list(row)

            valor = 0
            cliente = None
            cnpj = None
            placa = None
            cidade = None
            estado = None
            ano = None
            mes = None

            for celula in linha:

                texto = normalizar_texto_forte(celula)

                # VALOR
                num = extrair_numero_inteligente(celula)
                if num > 0:
                    valor = num

                # IDENTIFICAÇÃO
                tipo = detectar_tipo_dado(texto)
                if tipo:
                    tipo_id, dado = tipo

                    if tipo_id == "CNPJ":
                        cnpj = dado
                    elif tipo_id == "PLACA":
                        placa = dado
                    elif tipo_id == "NOME" and not cliente:
                        cliente = dado

                # ESTADO
                if len(texto) == 2 and texto.isalpha():
                    estado = texto

                # CIDADE
                if len(texto) > 4 and not cidade and not texto.isdigit():
                    cidade = texto

                # TEMPO LOCAL
                a, m = detectar_tempo_em_texto(texto)

                if a:
                    ano = a
                if m:
                    mes = m

            if valor <= 0:
                continue

            registros.append({
                "cliente": cliente,
                "cnpj": cnpj,
                "placa": placa,
                "cidade": cidade,
                "estado": estado,
                "valor": valor,
                "ano": ano,
                "mes": mes
            })

    # =========================
    # APLICA TEMPO GLOBAL SE NECESSÁRIO
    # =========================

    for r in registros:

        if not r["ano"]:
            r["ano"] = ano_global or datetime.now().year

        if not r["mes"]:
            r["mes"] = mes_global or datetime.now().month

    return registros


# ============================================================
# RESOLUÇÃO INTELIGENTE DE CNPJ
# ============================================================

def resolver_cnpj_v4(reg):

    if reg.get("cnpj"):
        return reg.get("cnpj")

    if reg.get("placa"):
        v = resolver_cliente_por_placa(reg.get("placa"))
        if v:
            return v.get("cnpj")

    if reg.get("cliente"):
        c = resolver_cliente_por_nome(reg.get("cliente"))
        if c:
            return c.get("cnpj")

    return None


# ============================================================
# HASH ANTI-DUPLICAÇÃO
# ============================================================

def gerar_hash_registro(reg):

    chave = f"{reg.get('cliente')}_{reg.get('cidade')}_{reg.get('valor')}_{reg.get('mes')}_{reg.get('ano')}"
    return hashlib.md5(chave.encode()).hexdigest()


# ============================================================
# ENDPOINT — PROCESSAMENTO UNIVERSAL V4
# ============================================================

@app.post("/cti/v4/processar-upload")
async def cti_v4_processar_upload(file: UploadFile = File(...), origem: str = "UPLOAD"):

    contents = await file.read()

    registros = ler_planilha_inteligente_v4(contents)

    if not registros:
        return {"status": "sem dados"}

    registros_final = []
    hashes = set()

    for r in registros:

        cnpj = resolver_cnpj_v4(r)
        ddd = obter_ddd_unificado(r.get("cidade"))

        registro = {
            "cliente": r.get("cliente"),
            "cnpj": cnpj,
            "cidade": r.get("cidade"),
            "uf": r.get("estado"),
            "ddd": ddd,
            "valor": r.get("valor"),
            "ano": r.get("ano"),
            "mes": r.get("mes"),
            "origem": origem,
            "created_at": datetime.now().isoformat()
        }

        h = gerar_hash_registro(registro)

        if h in hashes:
            continue

        hashes.add(h)
        registros_final.append(registro)

    batch_size = 500
    total = 0

    for i in range(0, len(registros_final), batch_size):

        batch = registros_final[i:i + batch_size]

        response = supabase.table("cti_unificado").insert(batch).execute()

        if response.data:
            total += len(response.data)

    return {
        "status": "CTI_V4_OK",
        "lidos": len(registros),
        "inseridos": total
    }

# ============================================================
# CTI CORE UNIFICADO — CONSOLIDAÇÃO TOTAL DO SISTEMA
# ============================================================

def normalizar_nome_core(nome):
    if not nome:
        return ""

    nome = normalizar_texto(nome)

    remover = [" LTDA", " EIRELI", " SA", " S/A", " ME", " EPP"]

    for r in remover:
        nome = nome.replace(r, "")

    return nome.strip()


def construir_mapa_contatos():

    contatos = select_all("contatos")

    mapa_nome = {}
    mapa_cnpj = {}

    for c in contatos:

        nome = normalizar_nome_core(c.get("cliente"))
        cnpj = re.sub(r"\D", "", str(c.get("cnpj")))

        if nome:
            mapa_nome[nome] = cnpj

        if cnpj:
            mapa_cnpj[cnpj] = nome

    return mapa_nome, mapa_cnpj


def resolver_cnpj_core(cliente, cnpj, mapa_nome):

    if cnpj:
        return re.sub(r"\D", "", str(cnpj))

    nome = normalizar_nome_core(cliente)

    return mapa_nome.get(nome)


def classificar_status(origem):

    if origem == "ANFIR":
        return "REALIZADO"

    if origem == "ANFIR_SEMANAL":
        return "PROVISORIO"

    if origem == "NEGOCIACAO":
        return "NEGOCIACAO"

    if origem == "FUNIL":
        return "INTENCAO"

    return "DESCONHECIDO"


@app.post("/cti/core/unificar")
def cti_core_unificar():

    mapa_nome, mapa_cnpj = construir_mapa_contatos()

    base_final = []

    # ========================================================
    # ANFIR FINAL
    # ========================================================

    anfirs = select_all("cti_anfir")

    for r in anfirs:

        cliente = r.get("cliente")
        cnpj = resolver_cnpj_core(cliente, r.get("cnpj"), mapa_nome)

        base_final.append({
            "cliente": cliente,
            "cnpj": cnpj,
            "cidade": r.get("cidade"),
            "uf": r.get("estado"),
            "ddd": r.get("ddd"),
            "origem": "ANFIR",
            "status": "REALIZADO",
            "valor": r.get("valor"),
            "ano": r.get("ano"),
            "mes": r.get("mes"),
            "linha": r.get("linha"),
            "oem": r.get("implementador")
        })

    # ========================================================
    # NEGOCIAÇÕES
    # ========================================================

    negociacoes = select_all("negociacoes")

    for n in negociacoes:

        cliente = n.get("cliente")
        cnpj = resolver_cnpj_core(cliente, n.get("cnpj"), mapa_nome)

        base_final.append({
            "cliente": cliente,
            "cnpj": cnpj,
            "cidade": n.get("cidade"),
            "uf": n.get("estado"),
            "ddd": None,
            "origem": "NEGOCIACAO",
            "status": "NEGOCIACAO",
            "valor": n.get("valor"),
            "ano": None,
            "mes": None,
            "linha": n.get("produto"),
            "oem": None
        })

    # ========================================================
    # FUNIL
    # ========================================================

    funil = select_all("funil")

    for f in funil:

        cliente = f.get("cliente")
        cnpj = resolver_cnpj_core(cliente, None, mapa_nome)

        base_final.append({
            "cliente": cliente,
            "cnpj": cnpj,
            "cidade": f.get("cidade"),
            "uf": None,
            "ddd": None,
            "origem": "FUNIL",
            "status": "INTENCAO",
            "valor": f.get("valor"),
            "ano": None,
            "mes": None,
            "linha": None,
            "oem": None
        })

    # ========================================================
    # LIMPA BASE ANTIGA
    # ========================================================

    supabase.table("cti_unificado")\
        .delete()\
        .gt("created_at", "1900-01-01")\
        .execute()

    # ========================================================
    # INSERT FINAL
    # ========================================================

    total = 0
    batch_size = 500

    for i in range(0, len(base_final), batch_size):

        batch = base_final[i:i + batch_size]

        response = supabase.table("cti_unificado").insert(batch).execute()

        if response.data:
            total += len(response.data)

    return {
        "status": "CTI_UNIFICADO_OK",
        "registros": total
    }

# =========================================================
# CORE UNIFICADO — ENGINE UNIVERSAL (SAFE MODE)
# =========================================================

def engine_universal_planilha(df, origem="desconhecido"):

    registros = []

    for _, row in df.iterrows():

        try:
            linha = {str(k).strip().lower(): v for k, v in row.items()}

            cliente = (
                linha.get("cliente")
                or linha.get("cliente final")
                or linha.get("razao social")
                or linha.get("nome")
                or ""
            )

            cnpj = (
                linha.get("cnpj")
                or linha.get("cpf/cnpj")
                or linha.get("documento")
                or ""
            )

            valor = (
                linha.get("valor")
                or linha.get("total")
                or linha.get("valor total")
                or 0
            )

            data = (
                linha.get("data")
                or linha.get("data venda")
                or linha.get("fechamento")
                or None
            )

            cidade = (
                linha.get("cidade")
                or linha.get("municipio")
                or ""
            )

            estado = (
                linha.get("estado")
                or linha.get("uf")
                or ""
            )

            registro = {
                "cliente": normalizar_texto(cliente),
                "cnpj": limpar_texto(cnpj),
                "data": data,
                "valor": float(limpar_valor(valor) or 0),
                "origem": origem,
                "cidade": normalizar_texto(cidade),
                "estado": normalizar_texto(estado),
                "extra": linha
            }

            if not registro["cliente"] and not registro["valor"]:
                continue

            registros.append(registro)

        except Exception as e:
            print("[ENGINE UNIVERSAL ERRO]", str(e))
            continue

    return registros


# =========================================================
# ENDPOINT UNIVERSAL
# =========================================================

@app.post("/upload/universal")
async def upload_universal(file: UploadFile = File(...), origem: str = "manual"):

    try:
        contents = await file.read()

        df = pd.read_excel(io.BytesIO(contents))
        df = df.fillna("")

        registros = engine_universal_planilha(df, origem)

        if not registros:
            return {"status": "erro", "mensagem": "nenhum dado válido"}

        total_inserido = 0
        batch_size = 500

        for i in range(0, len(registros), batch_size):

            batch = registros[i:i + batch_size]

            try:
                response = supabase.table("cti_dados").insert(batch).execute()

                if response.data:
                    total_inserido += len(response.data)

            except Exception as e:
                print("[ERRO INSERT UNIVERSAL]", str(e))

        return {
            "status": "PROCESSADO",
            "origem": origem,
            "extraidos": len(registros),
            "inseridos": total_inserido
        }

    except Exception as e:
        print("[ERRO GLOBAL UNIVERSAL]", str(e))
        raise HTTPException(status_code=500, detail=str(e))
