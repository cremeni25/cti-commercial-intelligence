# ============================================================
# CTI BACKEND V3.3 — INGESTÃO PROFISSIONAL (UPSERT + SEM GARGALO)
# ============================================================

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
import pandas as pd
import re
import hashlib
import uuid
from datetime import datetime
from io import BytesIO

# ============================================================
# CONFIG
# ============================================================

APP_NAME = "CTI — Commercial Tactical Intelligence"
APP_VERSION = "3.3"

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

def limpar_valor(v):
    try:
        return float(str(v).replace(",", "."))
    except:
        return 0.0

def gerar_hash_dict(reg):
    base = f"{reg.get('cliente')}_{reg.get('valor')}_{reg.get('data')}"
    return hashlib.md5(base.encode()).hexdigest()

def gerar_hash_linha(linha):
    return hashlib.sha256(linha.encode()).hexdigest()

def gerar_cliente_id():
    return f"CLI_{uuid.uuid4().hex[:8].upper()}"

# ============================================================
# DETECÇÃO DE COLUNAS
# ============================================================

def detectar_colunas(df):
    mapa = {}

    for col in df.columns:
        c = col.lower()

        if "cliente" in c:
            mapa["cliente"] = col
        elif "valor" in c or "total" in c:
            mapa["valor"] = col
        elif "data" in c:
            mapa["data"] = col

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
        valor = limpar_valor(row.get(mapa.get("valor", ""), 0))
        data = str(row.get(mapa.get("data", ""), ""))

        if not cliente and valor == 0:
            continue

        reg = {
            "cliente": cliente,
            "valor": valor,
            "data": data,
            "cliente_id": gerar_cliente_id(),
            "created_at": datetime.utcnow().isoformat()
        }

        reg["hash"] = gerar_hash_dict(reg)

        registros.append(reg)

    return registros

# ============================================================
# EXTRAÇÃO UNIVERSAL
# ============================================================

def extrair_linhas(conteudo: bytes, filename: str):

    nome = filename.lower()

    try:
        if nome.endswith(".xlsx") or nome.endswith(".xls"):
            df = pd.read_excel(BytesIO(conteudo), engine="openpyxl", dtype=str)

            linhas = []
            for _, row in df.iterrows():
                linha = " | ".join([str(v) for v in row.values if str(v) != "nan"])
                if linha.strip():
                    linhas.append(normalizar_texto(linha))

            return linhas

        else:
            texto = conteudo.decode("utf-8", errors="ignore")
            return [normalizar_texto(l) for l in texto.split("\n") if l.strip()]

    except Exception as e:
        log(f"Erro extração: {e}")
        return []

# ============================================================
# UPSERT (CORREÇÃO DEFINITIVA)
# ============================================================

def upsert_lote(tabela, dados, batch=500):

    total = 0

    for i in range(0, len(dados), batch):
        parte = dados[i:i+batch]

        res = supabase.table(tabela)\
            .upsert(parte, on_conflict="hash")\
            .execute()

        if res.data:
            total += len(res.data)

    return total

# ============================================================
# ENDPOINT PRINCIPAL
# ============================================================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    log(f"Upload: {file.filename}")

    try:

        conteudo = await file.read()

        # ===============================
        # ESTRUTURADO
        # ===============================
        try:
            df = pd.read_excel(BytesIO(conteudo), engine="openpyxl")

            registros = processar_dataframe(df)
            inseridos = upsert_lote("cti_dados", registros)

            return {
                "status": "estruturado",
                "lidos": len(registros),
                "inseridos": inseridos
            }

        except Exception as e:
            log(f"Fallback texto: {e}")

        # ===============================
        # TEXTO
        # ===============================
        linhas = extrair_linhas(conteudo, file.filename)

        registros = [{
            "hash": gerar_hash_linha(l),
            "conteudo": l,
            "created_at": datetime.utcnow().isoformat()
        } for l in linhas]

        inseridos = upsert_lote("cti_linhas", registros)

        return {
            "status": "texto",
            "lidos": len(linhas),
            "inseridos": inseridos
        }

    except Exception as e:
        import traceback
        erro = traceback.format_exc()

        log("ERRO CRÍTICO")
        log(erro)

        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": erro
        }

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
