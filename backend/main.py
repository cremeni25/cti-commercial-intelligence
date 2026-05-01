# ============================================================
# CTI BACKEND - BLOCO 1 (CORE)
# Arquitetura base estável
# ============================================================

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import hashlib
import os
import json
import re
import requests

# ============================================================
# APP
# ============================================================

app = FastAPI(title="CTI Comercial Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ENV / CONFIG
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase não configurado")

# ============================================================
# SUPABASE CLIENT
# ============================================================

from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# LOG PADRÃO
# ============================================================

def log(origem, nivel, mensagem):
    print(f"[{origem}] [{nivel}] {mensagem}")

# ============================================================
# UTILS
# ============================================================

def gerar_hash(texto):
    return hashlib.md5(texto.encode()).hexdigest()

def limpar_texto(texto):
    if not texto:
        return ""
    texto = str(texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def safe_upper(valor):
    if not valor:
        return None
    return str(valor).upper().strip()

# ============================================================
# NORMALIZAÇÃO BASE
# ============================================================

STOPWORDS_CLIENTE = [
    "UNIDADES", "SUDESTE", "SP", "BRASIL",
    "TRAILER", "DT", "DD", "DIRECT DRIVE",
    "DIESEL TRUCK", "VALOR", "PREÇO", "VENDA",
    "COTAÇÃO", "REGIAO", "FILIAL"
]

MARCAS_EQUIPAMENTO = [
    "CARRIER",
    "THERMO KING",
    "THERMOKING",
    "FRIGOKING",
    "THERMOSTAR",
    "RODOFRIO",
    "THERMOFLEX"
]

def validar_cliente(cliente):

    if not cliente:
        return None

    c = safe_upper(cliente)

    if not c:
        return None

    # tamanho mínimo
    if len(c) < 4:
        return None

    # marcas de equipamento (CRÍTICO)
    if any(marca in c for marca in MARCAS_EQUIPAMENTO):
        return None

    # lixo comum
    if any(x in c for x in [
        "PREÇO", "VALOR", "VENDA", "COTAÇÃO",
        "SOLUÇÃO", "PROBLEMA", "SEM", "NÃO"
    ]):
        return None

    # produto disfarçado
    if any(p in c for p in [
        "TR", "DT", "DD",
        "TRAILER", "DIESEL", "DIRECT"
    ]):
        return None

    return c

# ============================================================
# PRODUTO PADRÃO
# ============================================================

def normalizar_produto(produto):
    if not produto:
        return None

    p = safe_upper(produto)

    if "TRAILER" in p or p == "TR":
        return "TR"

    if "DIESEL" in p or p == "DT":
        return "DT"

    if "DIRECT" in p or p == "DD":
        return "DD"

    return None

# ============================================================
# BANCO
# ============================================================

def buscar_tabela(nome):
    try:
        return supabase.table(nome).select("*").execute().data or []
    except Exception as e:
        log("DB", "ERRO", str(e))
        return []

def inserir_lote(tabela, dados):
    if not dados:
        return 0

    try:
        supabase.table(tabela).insert(dados).execute()
        return len(dados)
    except Exception as e:
        log("DB", "ERRO INSERT", str(e))
        return 0

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "sistema": "CTI Comercial Intelligence",
        "versao": "3.0"
    }

# ============================================================
# STATUS
# ============================================================

@app.get("/status")
def status():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================
# CTI BACKEND - BLOCO 2 (IA + INTERPRETAÇÃO)
# Cérebro do sistema
# ============================================================

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# IA — INTERPRETAÇÃO CONTROLADA
# ============================================================

def interpretar_linha_com_ia(texto):

    if not texto:
        return {}

    try:

        prompt = f"""
Você é um sistema de inteligência comercial B2B do setor de transporte refrigerado.

Seu trabalho é extrair dados estruturados de uma linha de texto desorganizada.

REGRAS CRÍTICAS:

- CLIENTE deve ser EMPRESA REAL (transportadora, operador logístico, frigorífico)
- NÃO pode ser:
  - produto (TR, DT, DD, TRAILER, DIESEL, DIRECT)
  - observação (ex: preço alto, sem solução)
  - região (SP, SUDESTE, BRASIL)
  - palavras genéricas

- PRODUTO deve ser:
  - TR (Trailer)
  - DT (Diesel Truck)
  - DD (Direct Drive)

- MONTADORA:
  Ex: VOLVO, SCANIA, IVECO, VW

- IMPLEMENTADOR (OEM REAL):
  Ex: RANDON, FACCHINI, GUERRA

- Se não tiver certeza → retornar null

Retorne JSON válido:

{{
  "cliente": null,
  "produto": null,
  "montadora": null,
  "implementador": null,
  "cidade": null,
  "estado": null,
  "valor": null,
  "concorrente": null,
  "observacoes": null
}}

Texto:
{texto}
"""

        response = client.chat.completions.create(
            model="gpt-5.3-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        conteudo = response.choices[0].message.content

        try:
            dados = json.loads(conteudo)
            return dados if isinstance(dados, dict) else {}
        except:
            return {}

    except Exception as e:
        log("IA", "ERRO", str(e))
        return {}

# ============================================================
# LIMPEZA INTELIGENTE
# ============================================================

def sanitizar_dados_ia(d):

    if not isinstance(d, dict):
        return {}

    # CLIENTE
    cliente = validar_cliente(d.get("cliente"))

    # PRODUTO
    produto = normalizar_produto(d.get("produto"))

    # MONTADORA
    montadora = safe_upper(d.get("montadora"))

    # IMPLEMENTADOR (OEM)
    implementador = safe_upper(d.get("implementador"))

    # VALOR
    valor = d.get("valor")
    try:
        valor = float(valor)
    except:
        valor = 0

    # CIDADE / ESTADO
    cidade = safe_upper(d.get("cidade"))
    estado = safe_upper(d.get("estado"))

    # CONCORRENTE
    concorrente = safe_upper(d.get("concorrente"))

    return {
        "cliente": cliente,
        "produto": produto,
        "montadora": montadora,
        "implementador": implementador,
        "cidade": cidade,
        "estado": estado,
        "valor": valor,
        "concorrente": concorrente,
        "observacoes": d.get("observacoes")
    }

# ============================================================
# PIPELINE IA
# ============================================================

def processar_texto_com_ia(texto):

    texto_limpo = limpar_texto(texto)

    bruto = interpretar_linha_com_ia(texto_limpo)

    tratado = sanitizar_dados_ia(bruto)

    return tratado

# ============================================================
# CTI BACKEND - BLOCO 3 (PIPELINE OPERACIONAL)
# Upload + Processamento real
# ============================================================

import pandas as pd
from io import BytesIO

# ============================================================
# EXTRAÇÃO UNIVERSAL DE LINHAS
# ============================================================

def extrair_linhas_arquivo(conteudo: bytes, nome_arquivo: str):

    linhas = []

    try:

        if nome_arquivo.lower().endswith((".xlsx", ".xls")):

            xls = pd.ExcelFile(BytesIO(conteudo))

            for aba in xls.sheet_names:

                df = xls.parse(aba, dtype=str)
                df = df.fillna("")

                for _, row in df.iterrows():

                    linha = " | ".join([
                        str(v) for v in row.values if str(v).strip()
                    ])

                    if linha and len(linha) > 5:
                        linhas.append(linha)

        else:

            texto = conteudo.decode("utf-8", errors="ignore")

            for l in texto.split("\n"):
                if l.strip():
                    linhas.append(l.strip())

    except Exception as e:
        log("UPLOAD", "ERRO EXTRAÇÃO", str(e))

    return linhas

# ============================================================
# HASH REAL (SEM PERDA)
# ============================================================

def gerar_hash_unico(texto):
    return hashlib.sha256(texto.encode()).hexdigest()

# ============================================================
# INSERT SEGURO (SEM DESCARTE BURRO)
# ============================================================

def inserir_linhas_brutas(registros):

    if not registros:
        return 0

    inseridos = 0

    for i in range(0, len(registros), 500):
        lote = registros[i:i+500]

        try:
            res = supabase.table("cti_linhas") \
                .upsert(lote, on_conflict="hash") \
                .execute()

            inseridos += len(lote)

        except Exception as e:
            log("DB", "ERRO UPSERT", str(e))

    return inseridos

# ============================================================
# PROCESSAMENTO COMPLETO
# ============================================================

def processar_linhas_cti():

    dados = []
    pagina = 0
    limite = 1000

    # PAGINAÇÃO REAL
    while True:

        res = supabase.table("cti_linhas") \
            .select("*") \
            .range(pagina * limite, (pagina + 1) * limite - 1) \
            .execute()

        linhas = res.data or []

        if not linhas:
            break

        dados.extend(linhas)

        if len(linhas) < limite:
            break

        pagina += 1

    log("PIPELINE", "INFO", f"{len(dados)} linhas carregadas")

    novos = []

    for row in dados:

        texto = row.get("conteudo")

        if not texto:
            continue

        hash_linha = row.get("hash")

        try:

            d = processar_texto_com_ia(texto)

            registro = {
                "hash": hash_linha,
                "cliente": d.get("cliente"),
                "produto": d.get("produto"),
                "montadora": d.get("montadora"),
                "implementador": d.get("implementador"),
                "cidade": d.get("cidade"),
                "estado": d.get("estado"),
                "valor": d.get("valor") or 0,
                "concorrente": d.get("concorrente"),
                "observacoes": d.get("observacoes"),
                "conteudo_original": texto,
                "created_at": datetime.utcnow().isoformat()
            }

            novos.append(registro)

        except Exception as e:
            log("PIPELINE", "ERRO LINHA", str(e))
            continue

    inseridos = 0

    for i in range(0, len(novos), 500):
        lote = novos[i:i+500]

        try:
            res = supabase.table("cti_processado") \
                .upsert(lote, on_conflict="hash") \
                .execute()

            inseridos += len(lote)

        except Exception as e:
            log("DB", "ERRO PROCESSADO", str(e))

    log("PIPELINE", "INFO", f"{len(novos)} registros processados")
    log("DB", "INFO", f"{inseridos} inseridos no processado")
    
    return {
        "linhas_lidas": len(dados),
        "linhas_processadas": len(novos),
        "inseridos": inseridos
    }

# ============================================================
# ENDPOINT — UPLOAD
# ============================================================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    try:

        conteudo = await file.read()

        linhas = extrair_linhas_arquivo(conteudo, file.filename)

        registros = []

        for linha in linhas:

            registros.append({
                "hash": gerar_hash_unico(linha + file.filename + datetime.utcnow().isoformat()),
                "lote_id": datetime.utcnow().isoformat(),
                "conteudo": linha,
                "arquivo": file.filename,
                "created_at": datetime.utcnow().isoformat()
            })

        inseridos = inserir_linhas_brutas(registros)

        log("UPLOAD", "INFO", f"{len(registros)} enviados ao banco")
        log("DB", "INFO", f"{inseridos} inseridos")
        
        return {
            "status": "ok",
            "linhas_extraidas": len(linhas),
            "inseridos": inseridos
        }

    except Exception as e:
        return {
            "status": "erro",
            "mensagem": str(e)
        }

# ============================================================
# ENDPOINT — PROCESSAR
# ============================================================

@app.post("/processar")
def processar():

    resultado = processar_linhas_cti()

    return {
        "status": "ok",
        "resultado": resultado
    }

# ============================================================
# CTI BACKEND - BLOCO 4 (INTELIGÊNCIA + EXECUTIVO)
# Visualização e leitura estratégica
# ============================================================

from collections import Counter

# ============================================================
# BUSCA BASE PROCESSADA
# ============================================================

def carregar_base_processada():

    dados = []
    pagina = 0
    limite = 1000

    while True:

        res = supabase.table("cti_processado") \
            .select("*") \
            .range(pagina * limite, (pagina + 1) * limite - 1) \
            .execute()

        parte = res.data or []

        if not parte:
            break

        dados.extend(parte)

        if len(parte) < limite:
            break

        pagina += 1

    return dados

# ============================================================
# DASHBOARD EXECUTIVO
# ============================================================

@app.get("/dashboard/executivo")
def dashboard_executivo():

    data = carregar_base_processada()

    total = len(data)

    clientes = Counter()
    produtos = Counter()
    estados = Counter()
    montadoras = Counter()
    implementadores = Counter()
    concorrentes = Counter()

    faturamento_total = 0

    for row in data:

        cliente = row.get("cliente")
        produto = row.get("produto")
        estado = row.get("estado")
        montadora = row.get("montadora")
        implementador = row.get("implementador")
        concorrente = row.get("concorrente")
        valor = row.get("valor") or 0

        if cliente:
            clientes[cliente] += 1

        if produto:
            produtos[produto] += 1

        if estado:
            estados[estado] += 1

        if montadora:
            montadoras[montadora] += 1

        if implementador:
            implementadores[implementador] += 1

        if concorrente:
            concorrentes[concorrente] += 1

        try:
            faturamento_total += float(valor)
        except:
            pass

    # TOPS
    top_clientes = clientes.most_common(10)
    top_produtos = produtos.most_common(5)
    top_estados = estados.most_common(10)
    top_montadoras = montadoras.most_common(10)
    top_implementadores = implementadores.most_common(10)
    top_concorrentes = concorrentes.most_common(10)

    # TICKET MÉDIO
    ticket_medio = faturamento_total / total if total > 0 else 0

    return {
        "status": "ok",
        "resumo": {
            "total_registros": total,
            "faturamento_total": round(faturamento_total, 2),
            "ticket_medio": round(ticket_medio, 2)
        },
        "clientes": top_clientes,
        "produtos": top_produtos,
        "estados": top_estados,
        "montadoras": top_montadoras,
        "implementadores": top_implementadores,
        "concorrentes": top_concorrentes
    }

# ============================================================
# INSIGHTS AUTOMÁTICOS
# ============================================================

@app.get("/dashboard/insights")
def insights():

    data = carregar_base_processada()

    if not data:
        return {"status": "sem_dados"}

    clientes = Counter()
    estados = Counter()
    valores = []

    for row in data:

        if row.get("cliente"):
            clientes[row["cliente"]] += 1

        if row.get("estado"):
            estados[row["estado"]] += 1

        if row.get("valor"):
            try:
                valores.append(float(row["valor"]))
            except:
                pass

    top_cliente = clientes.most_common(1)
    top_estado = estados.most_common(1)

    ticket = sum(valores) / len(valores) if valores else 0

    return {
        "status": "ok",
        "leitura_estrategica": {
            "cliente_dominante": top_cliente[0][0] if top_cliente else None,
            "regiao_dominante": top_estado[0][0] if top_estado else None,
            "ticket_medio": round(ticket, 2),
            "recomendacoes": [
                "Expandir base de clientes" if len(clientes) < 10 else None,
                "Aumentar presença geográfica" if len(estados) < 5 else None,
                "Explorar grandes contas" if ticket > 10000 else None
            ]
        }
    }

# ============================================================
# DEBUG VISUAL (IMPORTANTE PRA VOCÊ)
# ============================================================

@app.get("/debug/amostra")
def debug_amostra():

    data = supabase.table("cti_processado") \
        .select("*") \
        .limit(20) \
        .execute().data or []

    return data

# ============================================================
# STATUS DO PIPELINE
# ============================================================

@app.get("/pipeline/status")
def pipeline_status():

    linhas = supabase.table("cti_linhas").select("id").execute().data or []
    processado = supabase.table("cti_processado").select("id").execute().data or []

    return {
        "linhas_brutas": len(linhas),
        "linhas_processadas": len(processado),
        "pipeline": "ativo"
    }

