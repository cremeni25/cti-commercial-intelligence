# ============================================================
# CTI BACKEND V3 — CORE CONSOLIDADO E ESTÁVEL (FINAL INTEGRADO)
# ============================================================

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
import pandas as pd
import io
import re
import hashlib
import uuid
from datetime import datetime
from io import BytesIO
from collections import Counter
import math

# ============================================================
# CONFIG
# ============================================================

APP_NAME = "CTI — Commercial Tactical Intelligence"
APP_VERSION = "4.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE não configurado")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# UTILS
# ============================================================

def log(msg):
    print(f"[CTI] [{datetime.utcnow()}] {msg}")

def normalizar_texto(txt):
    if not txt:
        return ""
    return re.sub(r"\s+", " ", str(txt).upper().strip())

def limpar_cnpj(cnpj):
    if not cnpj:
        return None
    cnpj = re.sub(r"\D", "", str(cnpj))
    return cnpj if len(cnpj) == 14 else None

def limpar_valor(v):
    try:
        return float(str(v).replace(",", "."))
    except:
        return None

def gerar_hash_dict(reg):
    base = f"{reg.get('cliente')}_{reg.get('cnpj')}_{reg.get('valor')}_{reg.get('data')}"
    return hashlib.md5(base.encode()).hexdigest()

def gerar_hash_linha(linha):
    return hashlib.sha256(linha.encode()).hexdigest()

def gerar_cliente_id():
    return f"CLI_{uuid.uuid4().hex[:8].upper()}"

# ============================================================
# INTELIGÊNCIA COMERCIAL
# ============================================================

OEMS = ["FACCHINI","RANDON","GUERRA","NOMA"]
LOCADORAS = ["LOCALIZA","UNIDAS","MOVIDA"]

def detectar_oem(texto):
    texto = texto.upper()
    for o in OEMS:
        if o in texto:
            return o
    return None

def detectar_locadora(texto):
    texto = texto.upper()
    for l in LOCADORAS:
        if l in texto:
            return l
    return None

def classificar_produto(texto):
    if not texto:
        return None
    t = texto.upper()
    if "SEMI" in t or "CARRETA" in t:
        return "TR"
    if "TRUCK" in t or "TOCO" in t:
        return "DT"
    if "DIRECT" in t:
        return "DD"
    return None

def classificar_canal(oem, locadora):
    if locadora:
        return "LOCADORA"
    if oem:
        return "OEM"
    return "DIRETO"

# ============================================================
# PARSER
# ============================================================

def extrair_campos(texto: str):

    if not texto:
        return {}

    texto_original = texto
    texto = normalizar_texto(texto)

    partes = [p.strip() for p in texto.split("|") if p.strip()]

    d = {
        "cliente": None,
        "produto": None,
        "modelo": None,
        "vendedor": None,
        "cidade": None,
        "estado": None,
        "ddd": None,
        "cnpj": None,
        "valor": None,
        "oem": None,
        "locadora": None,
        "concorrente": None,
        "zona": None,
        "data": None,
        "observacoes": texto_original
    }

    # POSICIONAL
    if len(partes) >= 3:
        if len(partes[2]) == 2:
            d["estado"] = partes[2]

    if len(partes) >= 4:
        d["cidade"] = partes[3]

    if len(partes) >= 5:
        d["oem"] = detectar_oem(partes[4]) or partes[4]

    if len(partes) >= 6:
        d["produto"] = partes[5]

    if len(partes) >= 7:
        d["modelo"] = partes[6]

    # REGEX
    def find(pattern):
        m = re.search(pattern, texto)
        return m.group(2).strip() if m else None

    d["cliente"] = find(r"(CLIENTE|EMPRESA)\s*[:\-]\s*([A-Z0-9\s]{3,60})")
    d["vendedor"] = find(r"(VENDEDOR|CONSULTOR)\s*[:\-]\s*([A-Z\s]{3,40})")
    d["locadora"] = find(r"(LOCADORA)\s*[:\-]\s*([A-Z0-9\s]{3,40})")
    d["concorrente"] = find(r"(CONCORRENTE)\s*[:\-]\s*([A-Z0-9\s]{3,40})")

    # CNPJ
    cnpj_match = re.search(r"\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2}", texto)
    if cnpj_match:
        d["cnpj"] = limpar_cnpj(cnpj_match.group(0))

    # VALOR
    valor_match = re.search(r"(\d{1,3}(?:[\.\,]\d{3})*(?:[\.\,]\d{2}))", texto)
    if valor_match:
        d["valor"] = limpar_valor(valor_match.group(1))

    # DDD
    ddd_match = re.search(r"\b(\d{2})\b", texto)
    if ddd_match:
        d["ddd"] = ddd_match.group(1)

    # ZONA
    if "ZONA LESTE" in texto:
        d["zona"] = "ZL"
    elif "ZONA OESTE" in texto:
        d["zona"] = "ZO"
    elif "ZONA SUL" in texto:
        d["zona"] = "ZS"
    elif "ZONA NORTE" in texto:
        d["zona"] = "ZN"

    # DATA
    data_match = re.search(r"\d{2}/\d{2}/\d{4}", texto)
    if data_match:
        d["data"] = data_match.group(0)

    # REGRAS CRÍTICAS
    if d["cliente"] and d["cliente"] in OEMS:
        d["cliente"] = None

    if d["produto"] and "BAU" in d["produto"]:
        d["produto"] = None

    d["produto"] = classificar_produto(texto)
    d["oem"] = d["oem"] or detectar_oem(texto)
    d["locadora"] = d["locadora"] or detectar_locadora(texto)
    d["canal"] = classificar_canal(d["oem"], d["locadora"])

    return d

# ============================================================
# DETECÇÃO DE COLUNAS
# ============================================================

def detectar_colunas(df):
    mapa = {}

    for col in df.columns:
        c = col.lower()

        if "cliente" in c:
            mapa["cliente"] = col
        elif "cnpj" in c:
            mapa["cnpj"] = col
        elif "valor" in c or "total" in c:
            mapa["valor"] = col
        elif "data" in c:
            mapa["data"] = col
        elif "cidade" in c:
            mapa["cidade"] = col
        elif "estado" in c or "uf" in c:
            mapa["estado"] = col
        elif "vendedor" in c:
            mapa["vendedor"] = col

    return mapa

# ============================================================
# PROCESSAMENTO ESTRUTURADO
# ============================================================

def processar_dataframe(df):

    df = df.fillna("")
    mapa = detectar_colunas(df)

    registros = []

    for _, row in df.iterrows():

        cliente = normalizar_texto(row.get(mapa.get("cliente", ""), ""))
        cnpj = limpar_cnpj(row.get(mapa.get("cnpj", ""), ""))
        valor = limpar_valor(row.get(mapa.get("valor", ""), 0))
        data = str(row.get(mapa.get("data", ""), ""))

        cidade = normalizar_texto(row.get(mapa.get("cidade", ""), ""))
        estado = normalizar_texto(row.get(mapa.get("estado", ""), ""))
        vendedor = normalizar_texto(row.get(mapa.get("vendedor", ""), ""))

        if not cliente and not valor:
            continue

        texto_base = " | ".join([str(v) for v in row.values if str(v).strip()])
        dados_extraidos = extrair_campos(texto_base)

        reg = {
            "cliente": cliente or dados_extraidos.get("cliente"),
            "cnpj": cnpj or dados_extraidos.get("cnpj"),
            "valor": valor or dados_extraidos.get("valor"),
            "data": data or dados_extraidos.get("data"),
            "cidade": cidade or dados_extraidos.get("cidade"),
            "estado": estado or dados_extraidos.get("estado"),
            "vendedor": vendedor or dados_extraidos.get("vendedor"),
            "produto": dados_extraidos.get("produto"),
            "modelo": dados_extraidos.get("modelo"),
            "oem": dados_extraidos.get("oem"),
            "locadora": dados_extraidos.get("locadora"),
            "canal": dados_extraidos.get("canal"),
            "zona": dados_extraidos.get("zona"),
            "observacoes": dados_extraidos.get("observacoes"),
            "cliente_id": gerar_cliente_id(),
            "created_at": datetime.utcnow().isoformat()
        }

        reg["hash"] = gerar_hash_dict(reg)

        registros.append(reg)

    return registros

# ============================================================
# PROCESSAMENTO TEXTO
# ============================================================

def extrair_linhas_from_bytes(conteudo: bytes, filename: str):

    nome = filename.lower()
    linhas = []

    if nome.endswith(".xlsx") or nome.endswith(".xls"):

        df = pd.read_excel(BytesIO(conteudo), dtype=str, engine="openpyxl")

        for _, row in df.iterrows():
            linha = " | ".join([str(v) for v in row.values if str(v) != "nan"])
            if linha.strip():
                linhas.append(normalizar_texto(linha))

    else:
        texto = conteudo.decode("utf-8", errors="ignore")
        linhas = [normalizar_texto(l) for l in texto.split("\n") if l.strip()]

    return linhas

# ============================================================
# BANCO
# ============================================================

def get_hashes_existentes(tabela):

    try:
        response = supabase.table(tabela).select("hash").execute()
        if not response.data:
            return set()
        return set([r["hash"] for r in response.data if r.get("hash")])
    except:
        return set()

def insert_lote(tabela, dados, batch=500):

    total = 0

    for i in range(0, len(dados), batch):
        parte = dados[i:i+batch]

        try:
            res = supabase.table(tabela).insert(parte).execute()
            if res.data:
                total += len(res.data)
        except Exception as e:
            print("[ERRO INSERT]", e)
            continue

    return total

# ============================================================
# UPLOAD PRINCIPAL
# ============================================================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    log(f"Upload recebido: {file.filename}")

    try:

        conteudo = await file.read()

        xls = pd.ExcelFile(BytesIO(conteudo), engine="openpyxl")

        registros = []

        for aba in xls.sheet_names:
            df = xls.parse(aba, dtype=str)
            df = df.fillna("")

            for _, row in df.iterrows():

                linha = " | ".join([str(v) for v in row.values if str(v).strip()])

                if not linha:
                    continue

                linha = normalizar_texto(linha)

                if len(linha) < 5:
                    continue

                if len(linha.split("|")) < 2:
                    continue

                registros.append({
                    "hash": gerar_hash_linha(linha),
                    "conteudo": linha,
                    "arquivo": file.filename,
                    "aba": aba,
                    "created_at": datetime.utcnow().isoformat()
                })

        inseridos = insert_lote("cti_linhas", registros)

        return {
            "status": "ok",
            "linhas_processadas": len(registros),
            "inseridos": inseridos
        }

    except Exception as e:
        import traceback
        erro = traceback.format_exc()

        print("[ERRO UPLOAD]")
        print(erro)

        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": erro
        }

# ============================================================
# PROCESSAMENTO BASE (PIPELINE PRINCIPAL)
# ============================================================

@app.post("/processar-base")
def processar_base():

    data = supabase.table("cti_linhas").select("*").execute().data or []

    # evita erro caso coluna hash não exista
    try:
        existentes = supabase.table("cti_processado").select("hash").execute().data or []
        hashes_existentes = set([e.get("hash") for e in existentes if e.get("hash")])
    except:
        hashes_existentes = set()

    novos = []

    for row in data:

        texto = row.get("conteudo", "")
        h = row.get("hash")

        if not texto:
            continue

        # fallback de hash
        if not h:
            h = gerar_hash_linha(texto)

        if h in hashes_existentes:
            continue

        d = extrair_campos(texto)

        reg = {
            "hash": h,
            "controle_id": None,
            "data": d.get("data"),
            "vendedor": d.get("vendedor"),
            "cliente": d.get("cliente"),
            "cnpj": d.get("cnpj"),
            "produto": d.get("produto"),
            "modelo": d.get("modelo"),
            "cidade": d.get("cidade"),
            "estado": d.get("estado"),
            "ddd": d.get("ddd"),
            "zona": d.get("zona"),
            "valor": d.get("valor"),
            "oem": d.get("oem"),
            "locadora": d.get("locadora"),
            "canal": d.get("canal"),
            "concorrente": d.get("concorrente"),
            "observacoes": d.get("observacoes"),
            "origem_arquivo": row.get("arquivo"),
            "aba_origem": row.get("aba"),
            "conteudo_original": texto,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None
        }

        novos.append(reg)

    inseridos = insert_lote("cti_processado", novos)

    return {
        "status": "ok",
        "linhas_lidas": len(data),
        "novos_processados": len(novos),
        "inseridos": inseridos
    }


# ============================================================
# INTELIGÊNCIA — CLIENTES
# ============================================================

@app.get("/inteligencia/clientes")
def inteligencia_clientes():

    data = supabase.table("cti_processado").select("*").execute().data or []

    compras = Counter()
    faturamento = {}

    for row in data:

        cliente = row.get("cliente")

        if not cliente:
            continue

        valor = float(row.get("valor") or 0)

        compras[cliente] += 1
        faturamento[cliente] = faturamento.get(cliente, 0) + valor

    ranking = []

    for cliente in compras:
        ranking.append({
            "cliente": cliente,
            "compras": compras[cliente],
            "faturamento": round(faturamento.get(cliente, 0), 2)
        })

    ranking.sort(key=lambda x: x["compras"], reverse=True)

    return {
        "status": "ok",
        "ranking": ranking
    }


# ============================================================
# INTELIGÊNCIA — PRODUTOS
# ============================================================

@app.get("/inteligencia/produtos")
def inteligencia_produtos():

    data = supabase.table("cti_processado").select("*").execute().data or []

    contador = Counter()

    for row in data:
        produto = row.get("produto")
        if produto:
            contador[produto] += 1

    return {
        "status": "ok",
        "ranking_produtos": contador.most_common(10)
    }


# ============================================================
# INTELIGÊNCIA — REGIÃO
# ============================================================

@app.get("/inteligencia/regiao")
def inteligencia_regiao():

    data = supabase.table("cti_processado").select("*").execute().data or []

    cidades = Counter()
    estados = Counter()

    for row in data:

        cidade = row.get("cidade")
        estado = row.get("estado")

        if cidade:
            cidades[cidade] += 1

        if estado:
            estados[estado] += 1

    return {
        "status": "ok",
        "top_cidades": cidades.most_common(10),
        "top_estados": estados.most_common(10)
    }


# ============================================================
# INTELIGÊNCIA — CANAL
# ============================================================

@app.get("/inteligencia/canais")
def inteligencia_canais():

    data = supabase.table("cti_processado").select("*").execute().data or []

    canais = Counter()

    for row in data:
        canal = row.get("canal")
        if canal:
            canais[canal] += 1

    return {
        "status": "ok",
        "canais": canais
    }


# ============================================================
# INTELIGÊNCIA — OEM / CONCORRÊNCIA
# ============================================================

@app.get("/inteligencia/oem")
def inteligencia_oem():

    data = supabase.table("cti_processado").select("*").execute().data or []

    oems = Counter()
    concorrentes = Counter()

    for row in data:

        oem = row.get("oem")
        concorrente = row.get("concorrente")

        if oem:
            oems[oem] += 1

        if concorrente:
            concorrentes[concorrente] += 1

    return {
        "status": "ok",
        "oem": oems.most_common(10),
        "concorrentes": concorrentes.most_common(10)
    }

# ============================================================
# INTELIGÊNCIA — MÉTRICAS GERAIS
# ============================================================

@app.get("/inteligencia/resumo")
def inteligencia_resumo():

    data = supabase.table("cti_processado").select("*").execute().data or []

    total = len(data)

    valores = []
    clientes = set()

    for row in data:
        v = row.get("valor")
        if v:
            valores.append(float(v))

        c = row.get("cliente")
        if c:
            clientes.add(c)

    faturamento = sum(valores) if valores else 0
    ticket_medio = faturamento / len(valores) if valores else 0

    return {
        "status": "ok",
        "total_registros": total,
        "clientes_unicos": len(clientes),
        "faturamento_total": round(faturamento, 2),
        "ticket_medio": round(ticket_medio, 2)
    }


# ============================================================
# INTELIGÊNCIA — DECISÕES
# ============================================================

@app.get("/inteligencia/decisoes")
def inteligencia_decisoes():

    data = supabase.table("cti_processado").select("*").execute().data or []

    if not data:
        return {"status": "sem_dados"}

    clientes = Counter()
    cidades = Counter()
    valores = []

    for row in data:

        if row.get("cliente"):
            clientes[row["cliente"]] += 1

        if row.get("cidade"):
            cidades[row["cidade"]] += 1

        if row.get("valor"):
            valores.append(float(row["valor"]))

    total_clientes = sum(clientes.values())
    top5 = clientes.most_common(5)
    top5_total = sum([c[1] for c in top5]) if top5 else 0

    concentracao = (top5_total / total_clientes) if total_clientes else 0

    ticket_medio = sum(valores) / len(valores) if valores else 0

    alertas = []
    oportunidades = []
    acoes = []

    # concentração
    if concentracao > 0.6:
        alertas.append("Alta dependência de poucos clientes")
        acoes.append("Expandir base de clientes")

    elif concentracao > 0.4:
        oportunidades.append("Base moderadamente concentrada")
        acoes.append("Aumentar penetração em novos clientes")

    # ticket
    if ticket_medio < 1000:
        alertas.append("Ticket médio baixo")
        acoes.append("Revisar estratégia comercial")

    elif ticket_medio > 10000:
        oportunidades.append("Alto valor por venda")
        acoes.append("Focar grandes contas")

    # geografia
    if len(cidades) < 5:
        alertas.append("Baixa presença geográfica")
        acoes.append("Expandir regiões")

    return {
        "status": "ok",
        "resumo": {
            "ticket_medio": round(ticket_medio, 2),
            "concentracao_clientes": round(concentracao, 3),
            "cidades_ativas": len(cidades)
        },
        "top_clientes": top5,
        "top_cidades": cidades.most_common(5),
        "alertas": alertas,
        "oportunidades": oportunidades,
        "acoes": list(set(acoes))
    }


# ============================================================
# ANALYTICS SIMPLES
# ============================================================

@app.get("/analytics/resumo")
def analytics():

    data = supabase.table("cti_processado").select("*").execute().data or []

    return {
        "total_linhas": len(data)
    }


# ============================================================
# ENDPOINT DE DEBUG (IMPORTANTE)
# ============================================================

@app.get("/debug/linhas")
def debug_linhas():

    data = supabase.table("cti_linhas").select("*").limit(20).execute().data or []

    return data


@app.get("/debug/processado")
def debug_processado():

    data = supabase.table("cti_processado").select("*").limit(20).execute().data or []

    return data


# ============================================================
# ENDPOINT DE REPROCESSAMENTO
# ============================================================

@app.post("/reprocessar")
def reprocessar():

    try:
        supabase.table("cti_processado").delete().neq("id", 0).execute()
    except:
        pass

    return processar_base()


# ============================================================
# STATUS
# ============================================================

@app.get("/")
def root():
    return {
        "sistema": APP_NAME,
        "versao": APP_VERSION,
        "status": "ativo"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# SEGURANÇA FINAL
# ============================================================

@app.get("/check")
def check():

    try:
        supabase.table("cti_linhas").select("id").limit(1).execute()
        return {"db": "ok"}
    except:
        return {"db": "erro"}


# ============================================================
# FIM DO SISTEMA
# ============================================================

    
