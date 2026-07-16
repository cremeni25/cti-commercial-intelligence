# ============================================================
# CTI - COMMERCIAL INTELLIGENCE
# Arquivo......: planilha_engine_viena.py
# Versão.......: 2.0.0
# Status.......: PRODUÇÃO
#
# Parser Oficial VIENA
#
# Responsabilidade:
#
# - Ler qualquer planilha VIENA
# - Detectar automaticamente o cabeçalho
# - Normalizar colunas
# - Converter registros CTI
# - Gerar hash
#
# NÃO:
#
# - grava banco
# - calcula score
# - gera inteligência
# ============================================================

import hashlib
import uuid
import re

from datetime import datetime
from io import BytesIO

from models.cti_record import CTIRecord

import pandas as pd


# ============================================================
# COLUNAS ACEITAS
# ============================================================

COLUNAS = {

    "DATA": [
        "DATA",
        "DATA VENDA",
        "DT VENDA",
        "EMISSAO"
    ],

    "RESPONSAVEL": [
        "RESPONSAVEL",
        "RESPONSÁVEL",
        "VENDEDOR",
        "CONSULTOR"
    ],

    "REGIAO": [
        "REGIAO",
        "REGIÃO"
    ],

    "ESTADO": [
        "ESTADO",
        "UF"
    ],

    "DDD": [
        "DDD"
    ],

    "MUNICIPIO": [
        "MUNICIPIO",
        "MUNICÍPIO",
        "CIDADE"
    ],

    "SUB_REGIAO": [
        "SUB REGIAO",
        "SUB-REGIAO",
        "SUBREGIAO"
    ],

    "CLIENTE": [
        "CLIENTE",
        "NOME_PROPRIETARIO",
        "NOME PROPRIETARIO",
        "PROPRIETARIO",
        "RAZAO SOCIAL",
        "RAZAO_SOCIAL"
    ],

    "CNPJ": [
        "CNPJ",
        "CNPJ FATURADO",
        "CNPJ_FATURADO"
    ],

    "FABRICANTE_CAMINHAO": [
        "FABRICANTE CAMINHAO",
        "FABRICANTE_CAMINHÃO"
    ],

    "MODELO_CAMINHAO": [
        "MODELO CAMINHAO",
        "MODELO_CAMINHÃO"
    ],

    "EIXO": [
        "EIXO"
    ],

    "TIPO_VEICULO": [
        "TIPO VEICULO",
        "TIPO_VEICULO"
    ],

    "PLACA": [
        "PLACA"
    ],

    "CHASSI": [
        "CHASSI"
    ],

    "IMPLEMENTADORA": [
        "IMPLEMENTADORA",
        "IMPLEMENTADOR"
    ],

    "STATUS": [
        "STATUS"
    ],

    "MOTIVO": [
        "MOTIVO"
    ],

    "OCORRENCIA": [
        "OCORRENCIA",
        "OCORRÊNCIA"
    ],

    "FABRICANTE_EQUIPAMENTO": [
        "FABRICANTE EQUIPAMENTO"
    ],

    "LINHA": [
        "LINHA DE PRODUTO",
        "LINHA",
        "PRODUTO"
    ],

    "MODELO": [
        "MODELO DE PRODUTO",
        "MODELO"
    ],

    "VALOR": [
        "VALOR",
        "VALOR VENDA",
        "VALOR_TOTAL"
    ]

}


# ============================================================
# NORMALIZA TEXTO
# ============================================================

def texto(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip()


def numero(valor):

    try:

        if pd.isna(valor):
            return 0.0

        if valor == "":
            return 0.0

        if isinstance(valor, str):

            valor = (
                valor
                .replace(".", "")
                .replace(",", ".")
                .replace("R$", "")
                .strip()
            )

        return float(valor)

    except Exception:

        return 0.0


def limpar_nome_coluna(nome):

    nome = texto(nome).upper()

    nome = re.sub(r"\s+", " ", nome)

    return nome.strip()


def extrair_ano(data):

    try:
        return pd.to_datetime(data).year
    except Exception:
        return None


def extrair_mes(data):

    try:
        return pd.to_datetime(data).month
    except Exception:
        return None


# ============================================================
# HASH DO REGISTRO
# ============================================================

def gerar_hash(registro):

    chave = "|".join([

        texto(registro.get("cliente")),
        texto(registro.get("placa")),
        texto(registro.get("chassi")),
        texto(registro.get("linha")),
        texto(registro.get("implementadora")),
        texto(registro.get("data_venda"))

    ])

    return hashlib.sha256(
        chave.encode("utf-8")
    ).hexdigest()


# ============================================================
# IDENTIFICADOR OPERACIONAL DO VEÍCULO
# ============================================================

def normalizar_chassi(chassi):

    return (
        texto(chassi)
        .upper()
        .replace("-", "")
        .replace(" ", "")
    )


def normalizar_placa(placa):

    return (
        texto(placa)
        .upper()
        .replace("-", "")
        .replace(" ", "")
    )


def gerar_id_operacional(registro):

    chassi = normalizar_chassi(
        registro.get("chassi")
    )

    placa = normalizar_placa(
        registro.get("placa")
    )

    if chassi and placa:

        chave = f"CHASSI_PLACA|{chassi}|{placa}"

    elif chassi:

        chave = f"CHASSI|{chassi}"

    elif placa:

        chave = f"PLACA|{placa}"

    else:

        chave = f"TEMP|{uuid.uuid4()}"

    return hashlib.sha256(
        chave.encode("utf-8")
    ).hexdigest()

# ============================================================
# LOCALIZA CABEÇALHO
# ============================================================

def localizar_cabecalho(df):

    melhor_linha = None
    maior_pontuacao = -1

    for indice in range(min(len(df), 30)):

        linha = df.iloc[indice].tolist()

        linha_normalizada = [
            limpar_nome_coluna(c)
            for c in linha
        ]

        pontuacao = 0

        for coluna in linha_normalizada:

            for aliases in COLUNAS.values():

                if coluna in aliases:

                    pontuacao += 1

        if pontuacao > maior_pontuacao:

            maior_pontuacao = pontuacao
            melhor_linha = indice

    return melhor_linha


# ============================================================
# NORMALIZA COLUNAS
# ============================================================

def normalizar_dataframe(df):

    cabecalho = localizar_cabecalho(df)

    if cabecalho is None:

        return None

    nomes = []

    for coluna in df.iloc[cabecalho]:

        nomes.append(
            limpar_nome_coluna(coluna)
        )

    df = df.iloc[cabecalho + 1:].copy()

    df.columns = nomes

    df = df.reset_index(drop=True)

    return df


# ============================================================
# PROCURA COLUNA POR ALIAS
# ============================================================

def localizar_coluna(df, aliases):

    for alias in aliases:

        if alias in df.columns:

            return alias

    return None


# ============================================================
# LÊ VALOR
# ============================================================

def campo(df, row, aliases):

    coluna = localizar_coluna(df, aliases)

    if coluna is None:

        return ""

    return row[coluna]


# ============================================================
# LINHAS INVÁLIDAS
# ============================================================

def linha_valida(registro):

    if (
        registro["cliente"] == ""
        and registro["placa"] == ""
        and registro["chassi"] == ""
    ):

        return False

    cliente = registro["cliente"].upper()

    lixo = [

        "TOTAL",

        "TOTAL GERAL",

        "SUBTOTAL",

        "GERAL",

        "RESUMO"

    ]

    if cliente in lixo:

        return False

    return True


# ============================================================
# CONVERTE LINHA
# ============================================================

def converter_registro(df, row, nome_aba):

    data_venda = texto(

        campo(

            df,

            row,

            COLUNAS["DATA"]

        )

    )

    registro = CTIRecord(

    # ======================================================
    # DADOS TEMPORAIS
    # ======================================================

    ano=extrair_ano(data_venda),
    mes=extrair_mes(data_venda),
    data_venda=data_venda,

    # ======================================================
    # OPERAÇÃO
    # ======================================================

    responsavel=texto(
        campo(df, row, COLUNAS["RESPONSAVEL"])
    ),

    # ======================================================
    # LOCALIZAÇÃO
    # ======================================================

    regiao=texto(
        campo(df, row, COLUNAS["REGIAO"])
    ),

    estado=texto(
        campo(df, row, COLUNAS["ESTADO"])
    ),

    ddd=texto(
        campo(df, row, COLUNAS["DDD"])
    ),

    cidade=texto(
        campo(df, row, COLUNAS["MUNICIPIO"])
    ),

    sub_regiao=texto(
        campo(df, row, COLUNAS["SUB_REGIAO"])
    ),

    # ======================================================
    # CLIENTE
    # ======================================================

    cliente=texto(
        campo(df, row, COLUNAS["CLIENTE"])
    ),

    cnpj=texto(
        campo(df, row, COLUNAS["CNPJ"])
    ),

    # ======================================================
    # VEÍCULO
    # ======================================================

    fabricante_caminhao=texto(
        campo(df, row, COLUNAS["FABRICANTE_CAMINHAO"])
    ),

    modelo_caminhao=texto(
        campo(df, row, COLUNAS["MODELO_CAMINHAO"])
    ),

    eixo=texto(
        campo(df, row, COLUNAS["EIXO"])
    ),

    tipo_veiculo=texto(
        campo(df, row, COLUNAS["TIPO_VEICULO"])
    ),

    placa=texto(
        campo(df, row, COLUNAS["PLACA"])
    ),

    chassi=texto(
        campo(df, row, COLUNAS["CHASSI"])
    ),

    # ======================================================
    # EQUIPAMENTO
    # ======================================================

    implementadora=texto(
        campo(df, row, COLUNAS["IMPLEMENTADORA"])
    ),

    fabricante_equipamento=texto(
        campo(df, row, COLUNAS["FABRICANTE_EQUIPAMENTO"])
    ),

    linha=texto(
        campo(df, row, COLUNAS["LINHA"])
    ),

    modelo=texto(
        campo(df, row, COLUNAS["MODELO"])
    ),

    # ======================================================
    # OPERAÇÃO
    # ======================================================

    status=texto(
        campo(df, row, COLUNAS["STATUS"])
    ),

    motivo=texto(
        campo(df, row, COLUNAS["MOTIVO"])
    ),

    ocorrencia=texto(
        campo(df, row, COLUNAS["OCORRENCIA"])
    ),

    valor=numero(
        campo(df, row, COLUNAS["VALOR"])
    ),

    # ======================================================
    # ORIGEM
    # ======================================================

    origem_dado="VIENA",

    arquivo_origem="PLANILHA_VIENA",

    aba_origem=nome_aba,

    versao_parser="2.0.0",

    pipeline="UPLOAD_VIENA",

    ativo=True,

    created_at=datetime.utcnow().isoformat()

)

    registro = registro.to_dict()

    registro["hash_registro"] = gerar_hash(
        registro
    )

    registro["id_operacional"] = gerar_id_operacional(
    registro
    )

    return registro


# ============================================================
# PROCESSA UMA ABA
# ============================================================

def processar_aba(df, nome_aba):

    df = normalizar_dataframe(df)

    if df is None:

        return []

    df = df.fillna("")

    registros = []

    for _, row in df.iterrows():

        registro = converter_registro(

            df,

            row,

            nome_aba

        )

        if linha_valida(registro):

            registros.append(registro)

    return registros

    # ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================

def processar_planilha_viena(contents):

    abas = pd.read_excel(

        BytesIO(contents),

        sheet_name=None,

        header=None,

        dtype=object

    )

    registros = []

    for nome_aba, df in abas.items():

        try:

            registros.extend(

                processar_aba(

                    df,

                    nome_aba

                )

            )

        except Exception:

            # Caso uma aba apresente problema,
            # continua processando as demais.
            continue

    # ========================================================
    # REMOVE DUPLICADOS DO ARQUIVO
    # ========================================================

    registros_unicos = []

    hashes = set()

    for registro in registros:

        chave = registro.get("hash_registro")

        if not chave:

            registros_unicos.append(registro)

            continue

        if chave in hashes:

            continue

        hashes.add(chave)

        registros_unicos.append(registro)

    # ========================================================
    # ORDENA POR DATA
    # ========================================================

    registros_unicos.sort(

        key=lambda r: (

            r.get("ano") or 0,

            r.get("mes") or 0,

            r.get("cliente") or ""

        )

    )

    return registros_unicos