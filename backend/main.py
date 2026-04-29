# ============================================================
# CTI BACKEND V3 — CORE CONSOLIDADO E ESTÁVEL (FINAL INTEGRADO)
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
from collections import Counter

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

def gerar_hash_linha(linha):
    return hashlib.sha256(linha.encode()).hexdigest()

# ============================================================
# BANCO
# ============================================================

def insert_lote(tabela, dados, batch=500):

    total = 0

    for i in range(0, len(dados), batch):
        parte = dados[i:i+batch]

        res = supabase.table(tabela).insert(parte).execute()

        if not hasattr(res, "data") or not res.data:
            raise Exception(f"ERRO REAL DE INSERT: {res}")

        total += len(res.data)

    return total

# ============================================================
# UPLOAD PRINCIPAL (CORRIGIDO)
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

            # ✅ CORREÇÃO AQUI (INDENTAÇÃO)
            for _, row in df.iterrows():

                linha = " | ".join([str(v) if str(v) != "nan" else "" for v in row.values])

                if not linha:
                    continue

                linha = normalizar_texto(linha)

                # FILTRO DE LIXO
                if "PERIODO" in linha or "REGIAO" in linha:
                    continue

                if linha.count("|") < 5:
                    continue

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
# PROCESSAMENTO BASE
# ============================================================

@app.post("/processar-base")
def processar_base():

    data = supabase.table("cti_linhas").select("*").execute().data or []

    novos = []

    for row in data:

        texto = row.get("conteudo", "")
        h = row.get("hash")

        if not texto:
            continue

        novos.append({
            "hash": h,
            "conteudo": texto,
            "arquivo": row.get("arquivo"),
            "aba": row.get("aba"),
            "created_at": datetime.utcnow().isoformat()
        })

    inseridos = insert_lote("cti_processado", novos)

    return {
        "status": "ok",
        "inseridos": inseridos
    }

# ============================================================
# DEBUG
# ============================================================

@app.get("/debug/linhas")
def debug_linhas():
    return supabase.table("cti_linhas").select("*").limit(20).execute().data

@app.get("/debug/processado")
def debug_processado():
    return supabase.table("cti_processado").select("*").limit(20).execute().data

# ============================================================
# HEALTH
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
# CHECK DB
# ============================================================

@app.get("/check")
def check():

    try:
        supabase.table("cti_linhas").select("id").limit(1).execute()
        return {"db": "ok"}
    except:
        return {"db": "erro"}
