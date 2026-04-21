# ============================================================
# CTI BACKEND V3 — CORE CONSOLIDADO E ESTÁVEL (CORRIGIDO)
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

# ============================================================
# CONFIG
# ============================================================

APP_NAME = "CTI — Commercial Tactical Intelligence"
APP_VERSION = "3.2"

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
        return 0.0

def gerar_hash_dict(reg):
    base = f"{reg.get('cliente')}_{reg.get('cnpj')}_{reg.get('valor')}_{reg.get('data')}"
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

        if not cliente and valor == 0:
            continue

        reg = {
            "cliente": cliente,
            "cnpj": cnpj,
            "valor": valor,
            "data": data,
            "cidade": cidade,
            "estado": estado,
            "cliente_id": gerar_cliente_id(),
            "created_at": datetime.utcnow().isoformat()
        }

        reg["hash"] = gerar_hash_dict(reg)

        registros.append(reg)

    return registros

# ============================================================
# PROCESSAMENTO TEXTO (CORRIGIDO)
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

    response = supabase.table(tabela).select("hash").execute()

    if not response.data:
        return set()

    return set([r["hash"] for r in response.data if r.get("hash")])

def insert_lote(tabela, dados, batch=500):

    total = 0

    for i in range(0, len(dados), batch):
        parte = dados[i:i+batch]

        for item in parte:
            try:
                res = supabase.table(tabela).insert(item).execute()
                if res.data:
                    total += 1
            except Exception:
                # duplicado ou erro → ignora
                continue

    return total

# ============================================================
# ENDPOINT PRINCIPAL (CORRIGIDO)
# ============================================================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    log(f"Upload recebido: {file.filename}")

    try:

        conteudo = await file.read()

        # ====================================================
        # TENTATIVA ESTRUTURADA
        # ====================================================
        try:
            df = pd.read_excel(BytesIO(conteudo), engine="openpyxl")
            registros = processar_dataframe(df)

            hashes_existentes = get_hashes_existentes("cti_dados")
            novos = [r for r in registros if r["hash"] not in hashes_existentes]

            inseridos = insert_lote("cti_dados", novos)

            return {
                "status": "estruturado",
                "lidos": len(registros),
                "inseridos": inseridos
            }

        except Exception as e:
            log(f"Falha estruturada, fallback texto: {e}")

        # ====================================================
        # FALLBACK TEXTO
        # ====================================================
        linhas = extrair_linhas_from_bytes(conteudo, file.filename)

        hashes_existentes = get_hashes_existentes("cti_linhas")

        novos = []
        for l in linhas:
            h = gerar_hash_linha(l)
            if h not in hashes_existentes:
                novos.append({
                    "hash": h,
                    "conteudo": l,
                    "created_at": datetime.utcnow().isoformat()
                })

        inseridos = insert_lote("cti_linhas", novos)

        return {
            "status": "texto",
            "lidos": len(linhas),
            "inseridos": inseridos
        }

    except Exception as e:
        import traceback
        erro = traceback.format_exc()

        print("[CTI] [ERRO]")
        print(erro)

        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": erro
        }

# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics/resumo")
def resumo():

    data = supabase.table("cti_dados").select("*").execute().data or []

    total = len(data)
    faturamento = sum([limpar_valor(d.get("valor")) for d in data])

    return {
        "total_registros": total,
        "faturamento": faturamento
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

@app.get("/inteligencia/resumo")
def inteligencia_resumo():

    data = supabase.table("cti_linhas").select("conteudo").limit(5000).execute().data or []

    total_linhas = len(data)

    palavras = {}
    valores = []

    for item in data:

        texto = item.get("conteudo", "")

        partes = texto.split("|")

        for p in partes:
            p = p.strip()

            # contagem de palavras
            if len(p) > 3:
                palavras[p] = palavras.get(p, 0) + 1

            # tentativa de valor
            try:
                v = float(p.replace(",", "."))
                valores.append(v)
            except:
                pass

    top_palavras = sorted(palavras.items(), key=lambda x: x[1], reverse=True)[:10]

    total_valor = sum(valores)

    return {
        "linhas_analisadas": total_linhas,
        "top_termos": top_palavras,
        "soma_valores_detectados": total_valor,
        "quantidade_valores": len(valores)
    }

# ============================================================
# CTI V4 — MULTI-ABAS + FILTRO INTELIGENTE (SAFE ADD-ON)
# NÃO SUBSTITUI NADA — APENAS EXPANDE
# ============================================================

import re
import hashlib
from datetime import datetime
from io import BytesIO
import pandas as pd

# ============================================================
# CONFIG DE ATIVAÇÃO
# ============================================================

CTI_MULTI_ABAS_ATIVO = False  # 🔴 começa desligado (SAFE)

# ============================================================
# UTILIDADES
# ============================================================

def cti_normalizar_texto(txt):
    return re.sub(r"\s+", " ", str(txt).upper().strip())

def cti_hash(texto):
    return hashlib.sha256(texto.encode()).hexdigest()

# ============================================================
# DETECÇÃO DE RELEVÂNCIA DE ABA
# ============================================================

def cti_aba_relevante(linhas):

    if not linhas:
        return False

    score = 0

    for l in linhas[:50]:

        if any(char.isdigit() for char in l):
            score += 1

        if len(l.split()) > 3:
            score += 1

    return score > 10

# ============================================================
# EXTRAÇÃO MULTI-ABAS
# ============================================================

def cti_extrair_multiplas_abas(conteudo: bytes):

    todas_linhas = []

    try:
        xls = pd.ExcelFile(BytesIO(conteudo))

        print(f"[CTI V4] Abas detectadas: {xls.sheet_names}")

        for aba in xls.sheet_names:

            try:
                df = pd.read_excel(xls, sheet_name=aba, dtype=str)
                df = df.fillna("")

                linhas = []

                for _, row in df.iterrows():
                    linha = " | ".join([str(v) for v in row.values if str(v).strip()])
                    if linha:
                        linhas.append(cti_normalizar_texto(linha))

                if cti_aba_relevante(linhas):
                    print(f"[CTI V4] Aba relevante: {aba} ({len(linhas)} linhas)")
                    todas_linhas.extend(linhas)
                else:
                    print(f"[CTI V4] Aba ignorada: {aba}")

            except Exception as e:
                print(f"[CTI V4] Erro na aba {aba}: {e}")

    except Exception as e:
        print(f"[CTI V4] Falha geral leitura Excel: {e}")

    return todas_linhas

# ============================================================
# ENDPOINT DE TESTE SEGURO (NÃO INTERFERE NO /upload)
# ============================================================

@app.post("/upload-v4-teste")
async def upload_v4_teste(file: UploadFile = File(...)):

    print(f"[CTI V4] Upload teste: {file.filename}")

    conteudo = await file.read()

    linhas = cti_extrair_multiplas_abas(conteudo)

    if not linhas:
        return {
            "status": "erro",
            "mensagem": "nenhuma linha extraída"
        }

    # NÃO grava no banco — apenas analisa
    preview = linhas[:20]

    return {
        "status": "ok",
        "total_linhas_extraidas": len(linhas),
        "preview": preview
    }

# ============================================================
# ENDPOINT REAL (OPCIONAL FUTURO)
# ============================================================

@app.post("/upload-v4")
async def upload_v4(file: UploadFile = File(...)):

    print(f"[CTI V4] Upload REAL: {file.filename}")

    try:

        conteudo = await file.read()

        linhas = cti_extrair_multiplas_abas(conteudo)

        if not linhas:
            return {
                "status": "erro",
                "mensagem": "nenhuma linha extraída"
            }

        hashes_existentes = set(
            [r["hash"] for r in supabase.table("cti_linhas").select("hash").execute().data or []]
        )

        novos = []

        for l in linhas:
            h = cti_hash(l)
            if h not in hashes_existentes:
                novos.append({
                    "hash": h,
                    "conteudo": l,
                    "created_at": datetime.utcnow().isoformat()
                })

        inseridos = 0

        if novos:
            try:
                res = supabase.table("cti_linhas").insert(novos).execute()
                if res.data:
                    inseridos = len(res.data)
            except Exception as e:
                print(f"[CTI V4] ERRO INSERT: {e}")
                return {
                    "status": "erro_insert",
                    "mensagem": str(e),
                    "novos_detectados": len(novos)
                }

        return {
            "status": "ok",
            "linhas_extraidas": len(linhas),
            "novos_detectados": len(novos),
            "novos_inseridos": inseridos
        }

    except Exception as e:
        import traceback
        erro = traceback.format_exc()

        print("[CTI V4] ERRO GERAL")
        print(erro)

        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": erro
        }
