# ============================================================
# CTI BACKEND - BLOCO 1 (CORE)
# Arquitetura base estável
# ============================================================

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
import hashlib
import os
import json
import re
import requests

from core.cti_taxonomy import (
   PRODUTOS,
   IMPLEMENTADORAS,
   FABRICANTES_EQUIPAMENTO,
   STATUS_OPERACIONAIS,
   LIXO_OPERACIONAL,
   normalizar_produto,
   normalizar_implementadora,
   fabricante_valido,
   status_valido,
   cliente_lixo
)

from core.score_engine import(
    calcular_score_registro, 
    consolidar_scores
)
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

from routers.crm_router import router as crm_router
from routers.analytics_router import router as analytics_router
from routers.engine_router import router as engine_router
from routers.negociacoes_router import router as negociacoes_router
from routers.clientes_router import router as clientes_router
from routers.vendas_router import router as vendas_router
from routers.upload_router import router as upload_router
from routers.cti_api_router import router as cti_api_router

app.include_router(crm_router)

app.include_router(analytics_router)
app.include_router(engine_router)
app.include_router(negociacoes_router)
app.include_router(clientes_router)
app.include_router(vendas_router)
app.include_router(upload_router)
app.include_router(cti_api_router)

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

def validar_cliente(cliente):

    if not cliente:
        return None

    c = safe_upper(cliente)

    if not c:
        return None

    # tamanho mínimo
    if len(c) < 4:
        return None

    if cliente_lixo(c):
        return None

    if fabricante_valido(c):
        return None

    if any(x in c for x in [
        "PREÇO",
        "VALOR",
        "VENDA",
        "COTAÇÃO",
        "SOLUÇÃO",
        "PROBLEMA",
        "SEM",
        "NÃO"
    ]):

        return None

    produto = normalizar_produto(c)

    if produto:
        return None

    return c

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

# ============================================================
# CLIENTE OPENAI
# Inicializa somente quando existir chave configurada
# ============================================================

client = None

if OPENAI_API_KEY:

    try:

        client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        print(
            "OpenAI inicializado."
        )

    except Exception as e:

        print(
            f"Falha ao inicializar OpenAI: {e}"
        )

        client = None

else:

    print(
        "OPENAI_API_KEY não configurada. IA desabilitada temporariamente."
    )

# ============================================================
# IA — INTERPRETAÇÃO CONTROLADA
# ============================================================

def interpretar_linha_com_ia(texto):

    if not texto:
        return {}

    if client is None:
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

def tokenizar_linha_cti(texto):

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

def extrair_registros_estruturados(conteudo: bytes, nome_arquivo: str):

    registros = []

    try:

        xls = pd.ExcelFile(BytesIO(conteudo))

        for aba in xls.sheet_names:

            df = xls.parse(aba, dtype=str)

            df.columns = [str(c).strip().upper() for c in df.columns]

            df = df.fillna("")

            for _, row in df.iterrows():

                registro = {

                    "data": row.get("DATA"),
                    "responsavel": row.get("RESPONSAVEL"),
                    "regiao": row.get("REGIAO"),
                    "estado": row.get("ESTADO"),
                    "ddd": row.get("DDD"),
                    "municipio": row.get("MUNICIPIO"),
                    "sub_regiao": row.get("SUB-REGIAO"),

                    "cnpj_faturado": row.get("CNPJ_FATURADO"),

                    "fabricante_caminhao": row.get("FABRICANTE CAMINHAO"),
                    "modelo_caminhao": row.get("MODELO CAMINHAO"),

                    "eixo": row.get("EIXO"),
                    "tipo_veiculo": row.get("TIPO_VEICULO"),

                    "chassi": row.get("CHASSI"),
                    "placa": row.get("PLACA"),

                    "implementadora": row.get("IMPLEMENTADORA"),

                    "nome_proprietario": row.get("NOME_PROPRIETARIO"),

                    "status": row.get("STATUS"),
                    "motivo": row.get("MOTIVO"),
                    "ocorrencia": row.get("OCORRENCIA"),

                    "fabricante_equipamento": row.get("FABRICANTE EQUIPAMENTO"),
                    "produto": row.get("PRODUTO"),
                    "modelo_equipamento": row.get("MODELO EQUIPAMENTO"),

                    "conteudo": " | ".join([
                        str(row.get("FABRICANTE EQUIPAMENTO", "")),
                        str(row.get("PRODUTO", "")),
                        str(row.get("MODELO EQUIPAMENTO", "")),
                        str(row.get("REGIAO", "")),
                        str(row.get("RESPONSAVEL", "")),
                        str(row.get("STATUS", "")),
                        str(row.get("MOTIVO", "")),
                        str(row.get("OCORRENCIA", ""))
                    ]),
                    
                    "valor": row.get("VALOR"),

                    "aba": aba,
                    "arquivo": nome_arquivo
                }

                registros.append(registro)

    except Exception as e:
        log("UPLOAD", "ERRO EXTRAÇÃO", str(e))

    return registros
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
                .insert(lote) \
                .execute()

            print("SUPABASE RESPONSE:", res)

            if hasattr(res, "error") and res.error:
                log("DB", "ERRO INSERT", str(res.error))
            else:
                inseridos += len(lote)

        except Exception as e:
            log("DB", "ERRO INSERT", str(e))

    return inseridos

# ============================================================
# PROCESSAMENTO COMPLETO
# ============================================================
# ============================================================
# PROCESSAMENTO COMPLETO
# ============================================================

def corrigir_partes(partes):

    partes = [p.strip() for p in partes if p.strip()]

    produtos_validos = ["TR", "DT", "DD"]

    # CASO NORMAL
    if len(partes) >= 6:
        return partes

    # LINHA CURTA / DESLOCADA
    if len(partes) == 3:

        fabricante = partes[0]
        modelo = partes[1]
        vendedor = partes[2]

        return [
            fabricante,
            None,
            modelo,
            None,
            vendedor,
            None,
            None,
            None
        ]

    # FALLBACK
    while len(partes) < 8:
        partes.append(None)

    return partes

# ============================================================
# TOKENIZAÇÃO CONTROLADA CTI
# ============================================================

def nucleo_semantico_cti(texto):

    if not texto:
        return {}

    partes = [
        p.strip()
        for p in texto.split("|")
        if p.strip()
    ]

    resultado = {
        "fabricante_equipamento": None,
        "produto": None,
        "modelo_equipamento": None,
        "regiao": None,
        "vendedor": None,
        "status": None,
        "motivo": None,
        "ocorrencia": None,
        "score_geral": 0.0
    }

    # ========================================================
    # PRESERVAÇÃO POSICIONAL
    # ========================================================

    if len(partes) > 0:
        resultado["fabricante_equipamento"] = partes[0]

    if len(partes) > 1:
        resultado["produto"] = partes[1]

    if len(partes) > 2:
        resultado["modelo_equipamento"] = partes[2]

    if len(partes) > 3:
        resultado["regiao"] = partes[3]

    if len(partes) > 4:
        resultado["vendedor"] = partes[4]

    if len(partes) > 5:
        resultado["status"] = partes[5]

    if len(partes) > 6:
        resultado["motivo"] = partes[6]

    if len(partes) > 7:
        resultado["ocorrencia"] = partes[7]

    # ========================================================
    # VALIDAÇÃO SEMÂNTICA
    # ========================================================

    score = 0

    fabricante = str(
        resultado.get("fabricante_equipamento") or ""
    ).upper()

    produto = str(
        resultado.get("produto") or ""
    ).upper()

    regiao = str(
        resultado.get("regiao") or ""
    ).upper()

    status = str(
        resultado.get("status") or ""
    ).upper()

    vendedor = resultado.get("vendedor")

    # FABRICANTES

    fabricantes_validos = [
        "CARRIER",
        "THERMOKING",
        "THERMO KING",
        "THERMOSTAR",
        "FRIGOKING",
        "RODOFRIO",
        "THERMOFLEX"
    ]

    if fabricante_valido(fabricante):
        score += 0.2

    # PRODUTO

    if produto in ["TR", "DT", "DD"]:
        score += 0.2

    # REGIÃO

    if "REGIAO" in regiao:
        score += 0.2

    # STATUS

    status_validos = [
        "APROVADO",
        "PERDIDO",
        "GANHO",
        "EM NEGOCIACAO",
        "SEM SOLUCAO TECNICA"
    ]

    if status_valido(status):
        score += 0.2

    # VENDEDOR

    if vendedor and len(str(vendedor).strip()) >= 3:
        score += 0.2

    resultado["score_geral"] = round(score, 2)

    return resultado

def processar_linhas_cti():
    dados = []
    pagina = 0
    limite = 1000

    # ========================
    # PAGINAÇÃO REAL
    # ========================
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

    # ========================
    # PROCESSAMENTO IA
    # ========================
    for row in dados:

        texto = row.get("conteudo")

        if not texto:
            continue

        hash_linha = row.get("hash")

        try:

            d = nucleo_semantico_cti(texto)

            # ====================================================
            # SCORE DE CONFIANÇA CTI
            # ====================================================

            confianca_fabricante = 0.5
            confianca_modelo = 0.5
            confianca_regiao = 0.5
            confianca_status = 0.5
            confianca_vendedor = 0.5

            fabricante = d.get("fabricante_equipamento")
            modelo = d.get("modelo_equipamento")
            regiao = d.get("regiao")
            status = d.get("status")
            vendedor = d.get("vendedor")

            # FABRICANTE

            if fabricante:

                if fabricante.upper() in [
                    "CARRIER",
                    "THERMOKING",
                    "THERMO KING",
                    "THERMOSTAR",
                    "FRIGOKING",
                    "RODOFRIO",
                    "THERMOFLEX"
                ]:
                    confianca_fabricante = 0.95

            # MODELO

            if modelo:

                if len(modelo.strip()) >= 4:
                    confianca_modelo = 0.90

            # REGIAO

            if regiao:

                if "REGIAO" in regiao.upper():
                    confianca_regiao = 0.90

            # STATUS

            if status:

                if status.upper() in [
                    "APROVADO",
                    "PERDIDO",
                    "GANHO",
                    "EM NEGOCIACAO",
                    "SEM SOLUCAO TECNICA"
                ]:
                    confianca_status = 0.95

            # VENDEDOR

            if vendedor:

                if len(vendedor.strip()) >= 3:
                    confianca_vendedor = 0.85

            # SCORE GERAL

            score_geral = round(
                (
                    confianca_fabricante +
                    confianca_modelo +
                    confianca_regiao +
                    confianca_status +
                    confianca_vendedor
                ) / 5,
                2
            )

            registro = {

                "fabricante_equipamento": d.get("fabricante_equipamento"),
                "produto": d.get("produto"),
                "modelo_equipamento": d.get("modelo_equipamento"),
                "regiao": d.get("regiao"),
                "vendedor": d.get("vendedor"),
                "status": d.get("status"),
                "motivo": d.get("motivo"),
                "ocorrencia": d.get("ocorrencia"),

                "conteudo_original": texto,
                "confianca_fabricante": confianca_fabricante,
                "confianca_modelo": confianca_modelo,
                "confianca_regiao": confianca_regiao,
                "confianca_status": confianca_status,
                "confianca_vendedor": confianca_vendedor,
                "score_geral": score_geral,

                "created_at": datetime.utcnow().isoformat()
            }

            registro["hash"] = gerar_hash_unico(
                json.dumps(registro, ensure_ascii=False, sort_keys=True)
            )

            novos.append(registro)

        except Exception as e:
            log("PIPELINE", "ERRO LINHA", str(e))
            print("TEXTO ORIGINAL:", texto)
            print("DADOS:", d if 'd' in locals() else None)
            continue

    # ========================
    # INSERT PROCESSADO
    # ========================
    inseridos = 0

    for i in range(0, len(novos), 500):
        lote = novos[i:i+500]

        try:
            res = supabase.table("cti_processado") \
                .insert(lote) \
                .execute()

            print("PROCESSADO RESPONSE:", res)

            if hasattr(res, "error") and res.error:
                log("DB", "ERRO PROCESSADO", str(res.error))
            else:
                inseridos += len(lote)
                
        except Exception as e:
            log("DB", "ERRO INSERT PROCESSADO", str(e))

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

        registros = extrair_registros_estruturados(conteudo, file.filename)
        
        for r in registros:

            texto_base = json.dumps(r, ensure_ascii=False)

            texto_hash = json.dumps(r, ensure_ascii=False, sort_keys=True)

            r["hash"] = gerar_hash_unico(texto_hash)

            r["created_at"] = datetime.utcnow().isoformat()

        inseridos = inserir_linhas_brutas(registros)

        log("UPLOAD", "INFO", f"{len(registros)} enviados ao banco")
        log("DB", "INFO", f"{inseridos} inseridos")
        
        return {
            "status": "ok",
            "linhas_extraidas": len(registros),
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

    base = []

    pagina = 0
    limite = 1000

    while True:

        response = (
            supabase
            .table("cti_anfir")
            .select("*")
            .eq("ativo", True)
            .range(
                pagina * limite,
                ((pagina + 1) * limite) - 1
            )
            .execute()
        )

        registros = response.data or []

        if not registros:
            break

        for r in registros:

            base.append({

                "ano": r.get("ano"),

                "mes": r.get("mes"),

                "cliente": r.get("cliente"),

                "cnpj": r.get("cnpj"),

                "estado": r.get("estado"),

                "cidade": r.get("cidade"),

                "ddd": r.get("ddd"),

                "regiao": r.get("regiao"),

                "implementadora": r.get("implementador"),

                "linha": r.get("linha"),

                "modelo": r.get("modelo"),

                "responsavel": r.get("responsavel"),

                "placa": r.get("placa"),

                "chassi": r.get("chassi"),

                "valor": float(r.get("valor") or 0),

                "data_venda": r.get("data_venda"),

                "origem": r.get(
                    "origem_dado",
                    "VIENA"
                )

            })

        if len(registros) < limite:
            break

        pagina += 1

    print(f"[DASHBOARD] {len(base)} registros carregados.")

    return base

# ============================================================
# DASHBOARD EXECUTIVO
# ============================================================

@app.get("/dashboard/executivo")
def dashboard_executivo():

    data = carregar_base_processada()

    total = len(data)

    clientes = Counter()
    linhas = Counter()
    estados = Counter()
    implementadoras = Counter()
    responsaveis = Counter()

    faturamento_total = 0

    for row in data:

        cliente = row.get("cliente")
        linha = row.get("linha")
        estado = row.get("estado")
        implementadora = row.get("implementadora")
        responsavel = row.get("responsavel")
        valor = row.get("valor") or 0

        if cliente:
            clientes[cliente] += 1

        if linha:
            linhas[linha] += 1

        if estado:
            estados[estado] += 1

        if implementadora:
            implementadoras[implementadora] += 1

        if responsavel:
            responsaveis[responsavel] += 1

        try:
            faturamento_total += float(valor)
        except Exception:
            pass

    ticket_medio = (
        faturamento_total / total
        if total
        else 0
    )

    return {

        "status": "ok",

        "resumo": {

            "total_registros": total,

            "faturamento_total": round(
                faturamento_total,
                2
            ),

            "ticket_medio": round(
                ticket_medio,
                2
            )
        },

        "clientes":
            clientes.most_common(10),

        "linhas":
            linhas.most_common(10),

        "estados":
            estados.most_common(10),

        "implementadoras":
            implementadoras.most_common(10),

        "responsaveis":
            responsaveis.most_common(10)
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

    dados = (
        supabase
        .table("cti_anfir")
        .select(
            """
            cliente,
            implementador,
            linha,
            modelo,
            estado,
            valor,
            score_operacional
            """
        )
        .eq("ativo", True)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    return dados.data or []

# ============================================================
# STATUS DO PIPELINE
# ============================================================

@app.get("/pipeline/status")
def pipeline_status():

    resposta = (
        supabase
        .table("cti_anfir")
        .select("id", count="exact")
        .eq("ativo", True)
        .limit(1)
        .execute()
    )

    total = resposta.count or 0

    return {
        "linhas_brutas": total,
        "linhas_processadas": total,
        "pipeline": "ativo"
    }

# ============================================================
# DASHBOARD EXECUTIVO V2 (SEM RISCO - NÃO ALTERA NADA EXISTENTE)
# ============================================================

from collections import Counter

def limpar_cliente_exec(cliente):

    if not cliente:
        return None

    c = str(cliente).upper().strip()

    if c in LIXO_CLIENTE_EXEC:
        return None

    if any(m in c for m in MARCAS_EQUIPAMENTO_EXEC):
        return None

    if len(c) < 4:
        return None

    return c

@app.get("/dashboard/executivo/v2")
def dashboard_executivo_v2():

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

        cliente = limpar_cliente_exec(row.get("cliente"))
        produto = normalizar_produto(row.get("produto"))

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

    return {
        "status": "ok",
        "resumo": {
            "total_registros": total,
            "faturamento_total": round(faturamento_total, 2),
            "ticket_medio": round(faturamento_total / total, 2) if total > 0 else 0
        },
        "clientes": clientes.most_common(10),
        "produtos": produtos.most_common(5),
        "estados": estados.most_common(10),
        "montadoras": montadoras.most_common(10),
        "implementadores": implementadores.most_common(10),
        "concorrentes": concorrentes.most_common(10)
    }
