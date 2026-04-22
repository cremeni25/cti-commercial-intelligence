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

def extrair_campos(texto: str):
    import re

    if not texto:
        return {
            "cliente": "nao_identificado",
            "produto": "nao_identificado",
            "estado": "nao_identificado",
            "valor": 0
        }

    # =========================
    # LIMPEZA BASE
    # =========================
    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)

    # remove caracteres estranhos
    texto = re.sub(r"[^a-z0-9\s\.\,\-\/]", " ", texto)

    # =========================
    # LISTAS DE CONTROLE
    # =========================
    palavras_lixo = [
        "telefone", "email", "contato", "visitar", "visita",
        "fenatran", "obrigado", "att", "segue", "prezado",
        "cotacao", "orcamento"
    ]

    estados_validos = [
        "sp","rj","mg","pr","rs","sc","ba","go","mt","ms","df",
        "es","pe","ce","pa","am","ma","pb","rn","al","pi","se","to","ro","ac","ap","rr"
    ]

    # =========================
    # CLIENTE (MULTI-ESTRATÉGIA)
    # =========================

    cliente = "nao_identificado"

    # padrão 1: cliente: nome
    match = re.search(r"(cliente|empresa)\s*[:\-]\s*([a-z0-9\s]{3,50})", texto)
    if match:
        cliente = match.group(2).strip()

    # padrão 2: linha começa com nome (ex: "empresa x comprou...")
    if cliente == "nao_identificado":
        match = re.match(r"^([a-z0-9\s]{3,40})\s+(comprou|adquiriu|fez|realizou)", texto)
        if match:
            cliente = match.group(1).strip()

    # =========================
    # LIMPEZA DO CLIENTE
    # =========================
    cliente = cliente.strip()

    # remove múltiplos espaços
    cliente = re.sub(r"\s+", " ", cliente)

    # filtros de qualidade
    if len(cliente) < 3:
        cliente = "nao_identificado"

    if any(p in cliente for p in palavras_lixo):
        cliente = "nao_identificado"

    # remove clientes inválidos tipo "n", "j", "ok"
    if re.fullmatch(r"[a-z]{1,2}", cliente):
        cliente = "nao_identificado"

    # =========================
    # PRODUTO (placeholder inteligente)
    # =========================
    produto = "nao_identificado"

    match = re.search(r"(produto|equipamento)\s*[:\-]\s*([a-z0-9\s\-]{3,40})", texto)
    if match:
        produto = match.group(2).strip()

    # =========================
    # ESTADO
    # =========================
    estado = "nao_identificado"

    match = re.search(r"\b(" + "|".join(estados_validos) + r")\b", texto)
    if match:
        estado = match.group(1)

    # =========================
    # VALOR
    # =========================
    valor = 0

    match = re.search(r"(\d{1,3}(?:[\.\,]\d{3})*(?:[\.\,]\d{2}))", texto)
    if match:
        try:
            valor = float(match.group(1).replace(".", "").replace(",", "."))
        except:
            valor = 0

    # =========================
    # RESULTADO FINAL
    # =========================
    return {
        "cliente": cliente,
        "produto": produto,
        "estado": estado,
        "valor": valor
    }

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

        texto_base = row.get("conteudo") or ""
        dados_extraidos = extrair_campos(texto_base)
        reg = {
            "cliente": cliente or dados_extraidos["cliente"],
            "cnpj": cnpj,
            "valor": valor if valor > 0 else dados_extraidos["valor"],
            "data": data,
            "cidade": cidade,
            "estado": estado or dados_extraidos["estado"],
            "produto": dados_extraidos["produto"],
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
        # LEITURA MULTI-ABAS (SEM ESTRUTURA — DEFINITIVO)
        # ====================================================

        xls = pd.ExcelFile(BytesIO(conteudo), engine="openpyxl")

        linhas = []
        registros = []

        for aba in xls.sheet_names:
            df = xls.parse(aba, dtype=str)
            df = df.fillna("")

            for _, row in df.iterrows():
                linha = " | ".join([str(v) for v in row.values if str(v).strip()])

                if not linha:
                    continue

                linha = linha.upper().strip()

                if len(linha) < 5:
                    continue

                if len(linha.split("|")) < 2:
                    continue

                linhas.append(linha)

                registros.append({
                    "linha": linha,
                    "aba": aba
                })

        print(f"[UPLOAD] Abas lidas: {len(xls.sheet_names)}")
        print(f"[UPLOAD] Linhas extraídas: {len(linhas)}")

        hashes_existentes = set()

        if len(linhas) < 50000:
            hashes_existentes = get_hashes_existentes("cti_linhas")

        novos = []

        for r in registros:
            base_hash = f"{r['linha']}|{r['aba']}|{datetime.utcnow().isoformat()}"
            h = gerar_hash_linha(base_hash)

            if h not in hashes_existentes:
                novos.append({
                    "hash": h,
                    "conteudo": r["linha"],
                    "arquivo": file.filename,
                    "aba": r["aba"],
                    "created_at": datetime.utcnow().isoformat()
                })

        inseridos = insert_lote("cti_linhas", novos)

        return {
            "status": "multi_aba_texto",
            "abas_lidas": len(xls.sheet_names),
            "lidos": len(linhas),
            "inseridos": inseridos
        }

    except Exception as e:
        import traceback
        erro = traceback.format_exc()

        print("[CTI] ERRO")
        print(erro)

        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": erro
        }       
        
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
                    "arquivo": file.filename,
                    "aba": "TEXTO",
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

# ============================================================
# V4 — SCORE INTELIGENTE (SEM DESCARTE DE DADOS)
# ============================================================

import math

def cti_tokenizar(texto: str):
    return [t for t in re.split(r"\W+", texto.upper()) if t]


def cti_score_linha(linha: str):

    tokens = cti_tokenizar(linha)

    tamanho = len(tokens)

    # diversidade (quantidade de tokens únicos)
    diversidade = len(set(tokens))

    # proporção diversidade
    diversidade_ratio = diversidade / tamanho if tamanho > 0 else 0

    # densidade numérica
    numeros = sum(1 for t in tokens if t.isdigit())
    densidade_numerica = numeros / tamanho if tamanho > 0 else 0

    # score base (ajustável)
    score = (
        (tamanho * 0.2) +
        (diversidade_ratio * 2) +
        (densidade_numerica * 1.5)
    )

    return {
        "tokens": tokens,
        "tamanho": tamanho,
        "diversidade": diversidade,
        "diversidade_ratio": round(diversidade_ratio, 3),
        "densidade_numerica": round(densidade_numerica, 3),
        "score": round(score, 3)
    }


@app.post("/upload-v4-score")
async def upload_v4_score(file: UploadFile = File(...)):

    print(f"[CTI V4 SCORE] Upload: {file.filename}")

    try:

        conteudo = await file.read()

        linhas = cti_extrair_multiplas_abas(conteudo)

        if not linhas:
            return {
                "status": "erro",
                "mensagem": "nenhuma linha encontrada"
            }

        enriquecidos = []

        for l in linhas:

            if not l or len(l.strip()) < 3:
                continue

            base = l.strip()

            meta = cti_score_linha(base)

            registro = {
                "hash": cti_hash(base),
                "conteudo": base,
                "tokens": meta["tokens"][:20],  # limita tamanho
                "tamanho": meta["tamanho"],
                "diversidade": meta["diversidade"],
                "score": meta["score"],
                "densidade_numerica": meta["densidade_numerica"],
                "created_at": datetime.utcnow().isoformat()
            }

            enriquecidos.append(registro)

        # evita duplicados
        hashes_existentes = set(
            [r["hash"] for r in supabase.table("cti_linhas").select("hash").execute().data or []]
        )

        novos = [r for r in enriquecidos if r["hash"] not in hashes_existentes]

        inseridos = 0

        if novos:
            try:
                # INSERT EM LOTE PARA EVITAR ERRO DE TAMANHO
                batch = 500
                for i in range(0, len(novos), batch):
                    parte = novos[i:i+batch]
                    res = supabase.table("cti_linhas").insert(parte).execute()
                    if res.data:
                        inseridos += len(res.data)

            except Exception as e:
                print("[CTI V4 SCORE] ERRO INSERT:", e)
                return {
                    "status": "erro_insert",
                    "mensagem": str(e),
                    "novos_detectados": len(novos)
                }

        return {
            "status": "ok",
            "linhas_originais": len(linhas),
            "linhas_processadas": len(enriquecidos),
            "novos_detectados": len(novos),
            "inseridos": inseridos,
            "preview": enriquecidos[:10]
        }

    except Exception as e:
        import traceback
        erro = traceback.format_exc()

        print("[CTI V4 SCORE] ERRO GERAL")
        print(erro)

        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": erro
        }

# ============================================================
# CTI V5 — INGESTÃO LIMPA (PIPELINE PARALELO)
# NÃO INTERFERE NO SISTEMA ATUAL
# ============================================================

@app.post("/upload-v5")
async def upload_v5(file: UploadFile = File(...)):

    print(f"[CTI V5] Upload: {file.filename}")

    try:
        conteudo = await file.read()

        xls = pd.ExcelFile(BytesIO(conteudo), engine="openpyxl")

        total_abas = len(xls.sheet_names)
        total_linhas = 0

        registros = []

        for aba in xls.sheet_names:
            df = xls.parse(aba, dtype=str)
            df = df.fillna("")

            for row in df.itertuples(index=False):

                valores = [str(v).strip() for v in row if str(v).strip()]

                if not valores:
                    continue

                linha = " | ".join(valores).upper()

                total_linhas += 1

                # HASH COM CONTEXTO (NÃO COLIDE)
                base_hash = f"{file.filename}|{aba}|{linha}"
                h = hashlib.sha256(base_hash.encode()).hexdigest()

                registros.append({
                    "hash": h,
                    "conteudo": linha,
                    "arquivo": file.filename,
                    "aba": aba,
                    "created_at": datetime.utcnow().isoformat()
                })

        print(f"[CTI V5] Abas: {total_abas}")
        print(f"[CTI V5] Linhas: {total_linhas}")

        # INSERT DIRETO (SEM CONSULTAR HASHES)
        inseridos = 0
        batch = 500

        for i in range(0, len(registros), batch):
            parte = registros[i:i+batch]

            try:
                res = supabase.table("cti_linhas").insert(parte).execute()
                if res.data:
                    inseridos += len(res.data)

            except Exception as e:
                print("[CTI V5] ERRO INSERT:", e)

        return {
            "status": "v5_ok",
            "abas_lidas": total_abas,
            "linhas_processadas": total_linhas,
            "linhas_inseridas": inseridos
        }

    except Exception as e:
        import traceback
        erro = traceback.format_exc()

        print("[CTI V5] ERRO GERAL")
        print(erro)

        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": erro
        }

# ============================================================
# CTI V6 — INTELIGÊNCIA DE PADRÕES (ENTERPRISE)
# ============================================================

from collections import Counter
import re

def extrair_valores(texto):
    valores = []
    partes = texto.split("|")

    for p in partes:
        p = p.strip().replace(",", ".")

        try:
            v = float(p)
            if v > 0:
                valores.append(v)
        except:
            continue

    return valores


def classificar_valor(v):
    if v < 1000:
        return "baixo"
    elif v < 5000:
        return "medio"
    elif v < 20000:
        return "alto"
    else:
        return "muito_alto"


def extrair_tokens_relevantes(texto):
    tokens = re.split(r"\W+", texto.upper())
    return [t for t in tokens if len(t) > 3 and not t.isdigit()]


@app.get("/inteligencia/padroes")
def inteligencia_padroes():

    data = supabase.table("cti_linhas").select("conteudo").limit(10000).execute().data or []

    total_linhas = len(data)

    contador_clientes = Counter()
    contador_cidades = Counter()
    contador_estados = Counter()
    contador_faixa_valor = Counter()

    todos_valores = []
    densidade_numerica = []

    for item in data:

        texto = item.get("conteudo", "")

        if not texto:
            continue

        partes = [p.strip() for p in texto.split("|") if p.strip()]

        # ===============================
        # VALORES
        # ===============================
        valores = extrair_valores(texto)

        if valores:
            todos_valores.extend(valores)

            for v in valores:
                faixa = classificar_valor(v)
                contador_faixa_valor[faixa] += 1

        # ===============================
        # DENSIDADE NUMÉRICA
        # ===============================
        tokens = texto.split()
        nums = sum(1 for t in tokens if re.search(r"\d", t))
        densidade = nums / len(tokens) if tokens else 0
        densidade_numerica.append(densidade)

        # ===============================
        # HEURÍSTICAS SIMPLES (PRÁTICAS)
        # ===============================
        for p in partes:

            p_upper = p.upper()

            # Cliente (strings grandes)
            if len(p_upper) > 8 and not re.search(r"\d", p_upper):
                contador_clientes[p_upper] += 1

            # Estado (UF)
            if len(p_upper) == 2:
                contador_estados[p_upper] += 1

            # Cidade (texto médio)
            if 4 <= len(p_upper) <= 20 and not re.search(r"\d", p_upper):
                contador_cidades[p_upper] += 1

    # ===============================
    # MÉTRICAS
    # ===============================

    ticket_medio = sum(todos_valores) / len(todos_valores) if todos_valores else 0

    concentracao_top5 = 0
    if contador_clientes:
        total_clientes = sum(contador_clientes.values())
        top5 = contador_clientes.most_common(5)
        top5_total = sum([c[1] for c in top5])
        concentracao_top5 = round(top5_total / total_clientes, 3)

    densidade_media = sum(densidade_numerica) / len(densidade_numerica) if densidade_numerica else 0

    return {
        "resumo_geral": {
            "total_linhas_analisadas": total_linhas,
            "ticket_medio": round(ticket_medio, 2),
            "total_valores_detectados": len(todos_valores),
            "densidade_numerica_media": round(densidade_media, 3)
        },

        "top_clientes": contador_clientes.most_common(10),

        "top_cidades": contador_cidades.most_common(10),

        "top_estados": contador_estados.most_common(10),

        "distribuicao_valores": dict(contador_faixa_valor),

        "insights": {
            "concentracao_top5_clientes": concentracao_top5,
            "base_concentrada": concentracao_top5 > 0.5,
            "alto_volume_dados": total_linhas > 5000
        }
    }

# ============================================================
# CTI V7 — MOTOR DE DECISÃO COMERCIAL
# ============================================================

@app.get("/inteligencia/decisoes")
def inteligencia_decisoes():

    data = supabase.table("cti_linhas").select("conteudo").limit(10000).execute().data or []

    if not data:
        return {
            "status": "sem_dados",
            "mensagem": "Nenhum dado disponível para análise"
        }

    from collections import Counter
    import re

    contador_clientes = Counter()
    contador_cidades = Counter()
    valores = []
    densidades = []

    for item in data:

        texto = item.get("conteudo", "")
        partes = [p.strip() for p in texto.split("|") if p.strip()]

        # valores
        for p in partes:
            try:
                v = float(p.replace(",", "."))
                if v > 0:
                    valores.append(v)
            except:
                pass

        # clientes / cidades
        for p in partes:
            p_upper = p.upper()

            if len(p_upper) > 8 and not re.search(r"\d", p_upper):
                contador_clientes[p_upper] += 1

            if 4 <= len(p_upper) <= 20 and not re.search(r"\d", p_upper):
                contador_cidades[p_upper] += 1

        # densidade numérica
        tokens = texto.split()
        nums = sum(1 for t in tokens if re.search(r"\d", t))
        densidade = nums / len(tokens) if tokens else 0
        densidades.append(densidade)

    return {
            "status": "ok"
        }

@app.get("/inteligencia/clientes")
def inteligencia_clientes():

    data = supabase.table("cti_linhas").select("conteudo").execute().data or []
    from collections import Counter

    compras = Counter()
    faturamento = {}

    for row in data:
        cliente = row.get("cliente")

        if not cliente or cliente == "nao_identificado":
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
  
    # =========================
    # MÉTRICAS
    # =========================

    total_clientes = sum(contador_clientes.values())
    top5 = contador_clientes.most_common(5)
    top5_total = sum([c[1] for c in top5]) if top5 else 0
    concentracao = (top5_total / total_clientes) if total_clientes else 0

    ticket_medio = sum(valores) / len(valores) if valores else 0
    densidade_media = sum(densidades) / len(densidades) if densidades else 0

    cidades_unicas = len(contador_cidades)

    # =========================
    # DECISÕES
    # =========================

    alertas = []
    oportunidades = []
    acoes = []

    # 🔴 CONCENTRAÇÃO
    if concentracao > 0.6:
        alertas.append("Alta dependência de poucos clientes")
        acoes.append("Expandir base ativa de clientes imediatamente")
    elif concentracao > 0.4:
        oportunidades.append("Base moderadamente concentrada")
        acoes.append("Aumentar penetração em novos clientes")

    # 💰 TICKET
    if ticket_medio < 1000:
        alertas.append("Ticket médio baixo")
        acoes.append("Revisar estratégia de precificação ou mix de produtos")
    elif ticket_medio > 10000:
        oportunidades.append("Alto valor por transação")
        acoes.append("Focar retenção e relacionamento com grandes contas")

    # 🌎 DISPERSÃO
    if cidades_unicas < 5:
        alertas.append("Baixa presença geográfica")
        acoes.append("Expandir atuação regional")
    elif cidades_unicas > 20:
        oportunidades.append("Boa capilaridade geográfica")
        acoes.append("Otimizar logística e segmentação regional")

    # 📊 QUALIDADE DE DADOS
    if densidade_media < 0.1:
        alertas.append("Baixa densidade de informação nas linhas")
        acoes.append("Melhorar qualidade dos dados de origem")
    else:
        oportunidades.append("Boa qualidade de dados disponíveis")

    # =========================
    # RESULTADO FINAL
    # =========================

    return {
        "resumo": {
            "ticket_medio": round(ticket_medio, 2),
            "concentracao_clientes": round(concentracao, 3),
            "cidades_ativas": cidades_unicas,
            "densidade_dados": round(densidade_media, 3)
        },

        "top_clientes": top5,
        "top_cidades": contador_cidades.most_common(5),

        "alertas": alertas,
        "oportunidades": oportunidades,
        "acoes_recomendadas": list(set(acoes))  # remove duplicadas
    }
