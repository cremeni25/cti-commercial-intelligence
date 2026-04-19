# ============================================================
# CTI BACKEND V3 — CORE LIMPO
# ============================================================

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os

APP_NAME = "CTI — Commercial Tactical Intelligence"
APP_VERSION = "3.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE não configurado")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

import pandas as pd
import io
import re
import hashlib
from datetime import datetime

def log(msg):
    print(f"[CTI] {datetime.now()} | {msg}")

def normalizar_texto(txt):
    if not txt:
        return ""
    txt = str(txt).upper().strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt

def limpar_cnpj(cnpj):
    if not cnpj:
        return None
    cnpj = re.sub(r"\D", "", str(cnpj))
    return cnpj if len(cnpj) == 14 else None

def limpar_valor(v):
    try:
        return float(str(v).replace(",", "."))
    except:
        return 0

def gerar_hash(reg):
    base = f"{reg.get('cliente')}_{reg.get('cnpj')}_{reg.get('valor')}_{reg.get('data')}"
    return hashlib.md5(base.encode()).hexdigest()

from pydantic import BaseModel

class UploadResponse(BaseModel):
    status: str
    total_lidos: int
    total_inseridos: int

def insert_batch(table, data, batch_size=500):

    total = 0

    for i in range(0, len(data), batch_size):

        batch = data[i:i+batch_size]

        response = supabase.table(table).insert(batch).execute()

        if response.data:
            total += len(response.data)

    return total


def get_existing_hashes():

    response = supabase.table("cti_dados").select("hash").execute()

    if not response.data:
        return set()

    return set([r["hash"] for r in response.data if r.get("hash")])

def detectar_colunas(df):

    mapa = {}

    for col in df.columns:
        col_lower = col.lower()

        if "cliente" in col_lower:
            mapa["cliente"] = col

        elif "cnpj" in col_lower:
            mapa["cnpj"] = col

        elif "valor" in col_lower or "total" in col_lower:
            mapa["valor"] = col

        elif "data" in col_lower:
            mapa["data"] = col

        elif "cidade" in col_lower:
            mapa["cidade"] = col

        elif "estado" in col_lower or "uf" in col_lower:
            mapa["estado"] = col

    return mapa


def processar_dataframe(df):

    mapa = detectar_colunas(df)

    registros = []

    for _, row in df.iterrows():

        cliente = normalizar_texto(row.get(mapa.get("cliente")))
        cnpj = limpar_cnpj(row.get(mapa.get("cnpj")))
        valor = limpar_valor(row.get(mapa.get("valor")))
        data = row.get(mapa.get("data"))

        cidade = normalizar_texto(row.get(mapa.get("cidade")))
        estado = normalizar_texto(row.get(mapa.get("estado")))

        if not cliente and valor == 0:
            continue

        reg = {
            "cliente": cliente,
            "cnpj": cnpj,
            "valor": valor,
            "data": str(data),
            "cidade": cidade,
            "estado": estado,
            "created_at": datetime.utcnow().isoformat()
        }

        reg["hash"] = gerar_hash(reg)

        registros.append(reg)

    return registros


def pipeline_upload(contents):

    df = pd.read_excel(io.BytesIO(contents))
    df = df.fillna("")

    registros = processar_dataframe(df)

    if not registros:
        raise HTTPException(400, "Nenhum dado válido")

    hashes_existentes = get_existing_hashes()

    novos = [r for r in registros if r["hash"] not in hashes_existentes]

    return registros, novos

import uuid

def gerar_cliente_id():
    return f"CLI_{uuid.uuid4().hex[:8].upper()}"

def aplicar_cliente_id(registros):

    for r in registros:
        if not r.get("cliente_id"):
            r["cliente_id"] = gerar_cliente_id()

    return registros

@app.post("/upload/universal")
async def upload_universal(file: UploadFile = File(...)):

    contents = await file.read()

    registros, novos = pipeline_upload(contents)

    novos = aplicar_cliente_id(novos)

    total = insert_batch("cti_dados", novos)

    log(f"Upload: {len(registros)} lidos | {total} inseridos")

    return {
        "status": "OK",
        "total_lidos": len(registros),
        "total_inseridos": total
    }

@app.get("/analytics/resumo")
def resumo():

    data = supabase.table("cti_dados").select("*").execute().data

    total = len(data)
    faturamento = sum([limpar_valor(d.get("valor")) for d in data])

    return {
        "total_registros": total,
        "faturamento": faturamento
    }

@app.get("/")
def status():
    return {
        "sistema": APP_NAME,
        "versao": APP_VERSION,
        "status": "ativo"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

