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
# CTI — PARSER ESTRUTURADO POR POSIÇÃO (OFICIAL)
# ============================================================

def extrair_campos(texto: str):

    if not texto:
        return {}

    texto_original = texto
    texto = normalizar_texto(texto)

    partes = [p.strip() for p in texto.split("|") if p.strip()]
    texto_full = " ".join(partes)

    # =========================
    # DATA
    # =========================
    data = None
    for p in partes:
        if re.search(r"\d{4}-\d{2}-\d{2}", p):
            data = p
            break
        if re.search(r"\d{2}/\d{2}/\d{4}", p):
            data = p
            break

    # =========================
    # VALOR
    # =========================
    valor = None
    for p in partes:
        if re.search(r"\d+[.,]\d{2}", p):
            try:
                valor = float(p.replace(".", "").replace(",", "."))
                break
            except:
                pass

    # =========================
    # ESTADO (UF)
    # =========================
    estado = None
    for p in partes:
        if len(p) == 2 and p.isalpha():
            estado = p
            break

    # =========================
    # CIDADE
    # =========================
    cidade = None
    if estado:
        for i, p in enumerate(partes):
            if p == estado and i > 0:
                cidade = partes[i-1]
                break

    # =========================
    # OEM
    # =========================
    oem = detectar_oem(texto_full)

    # =========================
    # LOCADORA
    # =========================
    locadora = detectar_locadora(texto_full)

    # =========================
    # PRODUTO
    # =========================
    produto = classificar_produto(texto_full)

    # =========================
    # CLIENTE (heurística)
    # =========================
    cliente = None
    for p in partes[::-1]:
        if len(p) > 5 and not re.search(r"\d", p):
            cliente = p
            break

    # =========================
    # VENDEDOR (heurística simples)
    # =========================
    vendedor = None
    if cliente:
        for p in partes:
            if p != cliente and len(p.split()) <= 3:
                vendedor = p
                break

    # =========================
    # CANAL
    # =========================
    canal = classificar_canal(oem, locadora)

    return {
        "data": data,
        "estado": estado,
        "cidade": cidade,
        "cliente": cliente,
        "vendedor": vendedor,
        "valor": valor,
        "produto": produto,
        "oem": oem,
        "locadora": locadora,
        "canal": canal,
        "observacoes": texto_original
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
            linha = " | ".join([str(v) if str(v) != "nan" else "" for v in row.values])
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

        print("\n==============================")
        print("ENVIANDO REGISTRO:")
        print(parte)

        res = supabase.table(tabela).insert(parte).execute()

        print("RESPOSTA SUPABASE:")
        print(res)

        # SE NÃO INSERIU, QUEBRA NA HORA
        if not hasattr(res, "data") or not res.data:
            raise Exception(f"ERRO REAL DE INSERT: {res}")

        total += len(res.data)

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

                linha = " | ".join([str(v) if str(v) != "nan" else "" for v in row.values])

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

    data = buscar_todas_linhas("cti_linhas")
    
    # evita erro caso coluna hash não exista
    try:
        existentes = supabase.table("cti_processado").select("hash").execute().data or []
        hashes_existentes = set([e.get("hash") for e in existentes if e.get("hash")])
    except:
        hashes_existentes = set()

    novos = []

    for row in data:
        try:
            texto = row.get("conteudo", "")
            h = row.get("hash")

            if not texto:
                continue

            if not h:
                h = gerar_hash_linha(texto)

            if h in hashes_existentes:
                continue

            d = extrair_campos_seguro(texto)
            d = enriquecer_classificacao(d, texto)
            d = sanitizar_campos(d, texto)
            
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

        except Exception as e:
            print("[ERRO LINHA]", str(e))
            continue

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

# ============================================================
# EXTENSÃO CTI — UPLOAD AVANÇADO (ZIP + MULTI)
# NÃO SUBSTITUI O /upload ORIGINAL
# ============================================================

import zipfile

@app.post("/upload-avancado")
async def upload_avancado(file: UploadFile = File(...)):

    log(f"[AVANCADO] Upload recebido: {file.filename}")

    try:

        conteudo = await file.read()
        registros = []

        arquivos = []

        # ====================================================
        # SUPORTE A ZIP
        # ====================================================
        if file.filename.lower().endswith(".zip"):

            with zipfile.ZipFile(BytesIO(conteudo)) as z:

                for nome in z.namelist():
                    if nome.endswith(".xlsx") or nome.endswith(".xls"):
                        arquivos.append((nome, z.read(nome)))

        else:
            arquivos.append((file.filename, conteudo))

        # ====================================================
        # PROCESSAMENTO
        # ====================================================
        for nome_arquivo, conteudo_arquivo in arquivos:

            linhas = extrair_linhas_from_bytes(conteudo_arquivo, nome_arquivo)

            for linha in linhas:

                if len(linha) < 5:
                    continue

                if linha.count("|") < 2:
                    continue

                registros.append({
                    "hash": gerar_hash_linha(linha),
                    "conteudo": linha,
                    "arquivo": nome_arquivo,
                    "aba": "AUTO",
                    "created_at": datetime.utcnow().isoformat()
                })

        # ====================================================
        # UPSERT (NÃO QUEBRA O SISTEMA ATUAL)
        # ====================================================
        total = 0

        for i in range(0, len(registros), 500):
            parte = registros[i:i+500]

            res = supabase.table("cti_linhas") \
                .upsert(parte, on_conflict="hash") \
                .execute()

            if hasattr(res, "data") and res.data:
                total += len(res.data)

        return {
            "status": "ok",
            "arquivos_processados": len(arquivos),
            "linhas": len(registros),
            "inseridos": total
        }

    except Exception as e:
        import traceback
        return {
            "status": "erro",
            "mensagem": str(e),
            "trace": traceback.format_exc()
        }


# ============================================================
# EXTENSÃO CTI — INSIGHTS (LEITURA HUMANA)
# ============================================================

@app.get("/insights-avancado")
def insights_avancado():

    data = supabase.table("cti_processado").select("*").execute().data or []

    if not data:
        return {"status": "sem_dados"}

    clientes = Counter()
    estados = Counter()
    oems = Counter()
    valores = []

    for row in data:

        if row.get("cliente"):
            clientes[row["cliente"]] += 1

        if row.get("estado"):
            estados[row["estado"]] += 1

        if row.get("oem"):
            oems[row["oem"]] += 1

        if row.get("valor"):
            valores.append(float(row["valor"]))

    top_cliente = clientes.most_common(1)
    top_estado = estados.most_common(1)
    top_oem = oems.most_common(1)

    ticket = sum(valores)/len(valores) if valores else 0

    return {
        "status": "ok",
        "insight": {
            "cliente_dominante": top_cliente[0][0] if top_cliente else None,
            "regiao_forte": top_estado[0][0] if top_estado else None,
            "oem_dominante": top_oem[0][0] if top_oem else None,
            "ticket_medio": round(ticket, 2),
            "leitura": f"""
O CTI identificou concentração no cliente {top_cliente[0][0] if top_cliente else 'N/A'},
com forte atuação na região {top_estado[0][0] if top_estado else 'N/A'}.

O OEM predominante é {top_oem[0][0] if top_oem else 'N/A'}.

Ticket médio aproximado de {round(ticket,2)}.

Ação recomendada:
- Avaliar dependência de cliente
- Expandir atuação geográfica
- Mapear concorrência direta
"""
        }
    }


# ============================================================
# EXTENSÃO CTI — STATUS AVANÇADO
# ============================================================

@app.get("/status-avancado")
def status_avancado():

    linhas = supabase.table("cti_linhas").select("id").execute().data or []
    processado = supabase.table("cti_processado").select("id").execute().data or []

    return {
        "linhas_brutas": len(linhas),
        "linhas_processadas": len(processado),
        "pipeline": "ativo"
    }

# ==========================================
# PATCH BLINDAGEM PROCESSAMENTO
# ==========================================

def extrair_campos_seguro(texto):
    try:
        d = extrair_campos(texto)  # CORRETO
        if not isinstance(d, dict):
            return {}
        return d
    except Exception as e:
        print("[ERRO extrair_campos]", str(e))
        return {}

# =========================================
# EXTENSÃO CTI — CLASSIFICAÇÃO SEMÂNTICA
# =========================================

def enriquecer_classificacao(d, texto):
    try:
        texto_upper = texto.upper()

        cliente = d.get("cliente")
        produto = d.get("produto")

        # CLASSIFICAÇÃO DE PRODUTO (CARRIER)
        if any(p in texto_upper for p in ["TRAILER", " TR "]):
            produto = "TRAILER"

        elif any(p in texto_upper for p in ["DIESEL", "DT"]):
            produto = "DIESEL TRUCK"

        elif any(p in texto_upper for p in ["DIRECT", "DD"]):
            produto = "DIRECT DRIVE"

        # PROTEÇÃO CONTRA ERRO DE CLIENTE
        if cliente and cliente.upper() in [
            "TRAILER", "TR", "DT", "DD", "DIESEL", "DIRECT"
        ]:
            cliente = None

        d["cliente"] = cliente
        d["produto"] = produto

        return d

    except:
        return d

# =========================================
# EXTENSÃO CTI — SANITIZAÇÃO DE ENTIDADES
# =========================================

def sanitizar_campos(d, texto):
    try:
        cliente = d.get("cliente")
        produto = d.get("produto")

        texto_upper = texto.upper()

        # LISTA REAL DE PRODUTOS (Carrier)
        produtos_validos = [
            "TRAILER", "TR",
            "DIESEL", "DT",
            "DIRECT", "DD"
        ]

        # 🔴 REGRA 1 — cliente não pode ser produto
        if cliente and any(p == cliente.upper() for p in produtos_validos):
            cliente = None

        # 🔴 REGRA 2 — se produto não está definido, tenta identificar
        if not produto:
            if "TRAILER" in texto_upper or " BAU " in texto_upper:
                produto = "TRAILER"
            elif "DIESEL" in texto_upper or " 4X2" in texto_upper or "6X2" in texto_upper:
                produto = "DIESEL TRUCK"
            elif "DIRECT" in texto_upper:
                produto = "DIRECT DRIVE"

        d["cliente"] = cliente
        d["produto"] = produto

        return d

    except:
        return d

# =========================================
# EXTENSÃO CTI — PAGINAÇÃO COMPLETA
# =========================================

def buscar_todas_linhas(nome_tabela):
    try:
        tudo = []
        offset = 0
        limite = 1000

        while True:
            res = supabase.table(nome_tabela) \
                .select("*") \
                .range(offset, offset + limite - 1) \
                .execute()

            dados = res.data or []

            if not dados:
                break

            tudo.extend(dados)

            if len(dados) < limite:
                break

            offset += limite

        return tudo

    except Exception as e:
        print("ERRO PAGINAÇÃO:", e)
        return []
