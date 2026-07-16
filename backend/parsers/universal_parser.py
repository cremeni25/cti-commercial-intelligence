import pandas as pd
from io import BytesIO


PRODUTOS_ALIAS = {

    "TR": "TRAILER",
    "TRAILER": "TRAILER",
    "SEMI REBOQUE": "TRAILER",

    "DT": "DIESEL TRUCK",
    "DIESEL": "DIESEL TRUCK",
    "DIESEL TRUCK": "DIESEL TRUCK",

    "DD": "DIRECT DRIVE",
    "DIRECT": "DIRECT DRIVE",
    "DIRECT DRIVE": "DIRECT DRIVE"
}


IMPLEMENTADORAS_ALIAS = {

    "RANDON": "RANDON",
    "RANDON IMPLEMENTOS": "RANDON",

    "IBIPORA": "IBIPORÃ",
    "IBIPORÃ": "IBIPORÃ",

    "SULBRASIL": "SULBRASIL",

    "MERCOSUL": "MERCOSUL",

    "NIJU": "NIJU",

    "FACCHINI": "FACCHINI",

    "FIBRASIL": "FIBRASIL",

    "LABONIA": "LABONIA",

    "HC": "HC",

    "PAVAN": "PAVAN"
}


def normalizar_colunas(df):

    df.columns = [
        str(c)
        .strip()
        .upper()
        .replace("Ç", "C")
        .replace("Ã", "A")
        for c in df.columns
    ]

    return df


def detectar_coluna(df, palavras):

    for coluna in df.columns:

        for palavra in palavras:

            if palavra in coluna:
                return coluna

    return None


def detectar_mapeamento(df):

    mapa = {}

    mapa["estado"] = detectar_coluna(df, [

        "UF",
        "ESTADO",
        "UF DESTINO",
        "ESTADO CLIENTE"

    ])

    mapa["linha"] = detectar_coluna(df, [

        "LINHA",
        "PRODUTO",
        "TIPO IMPLEMENTO",
        "IMPLEMENTO"

    ])

    mapa["implementadora"] = detectar_coluna(df, [

        "IMPLEMENTADORA",
        "FABRICANTE",
        "MARCA",
        "OEM",
        "IMPLEMENTADOR"

    ])

    mapa["valor"] = detectar_coluna(df, [

        "VALOR",
        "VALOR TOTAL",
        "VALOR UNIT",
        "PRECO",
        "PREÇO"

    ])

    return mapa


def normalizar_produto(valor):

    if not valor:
        return ""

    valor = (
        str(valor)
        .strip()
        .upper()
    )

    return PRODUTOS_ALIAS.get(
        valor,
        valor
    )


def normalizar_implementadora(valor):

    if not valor:
        return ""

    valor = (
        str(valor)
        .strip()
        .upper()
    )

    return IMPLEMENTADORAS_ALIAS.get(
        valor,
        valor
    )


def processar_planilha_universal(contents):

    df = pd.read_excel(
        BytesIO(contents)
    )

    df = normalizar_colunas(df)

    mapa = detectar_mapeamento(df)

    registros = []

    for _, row in df.iterrows():

        estado = (
            row.get(mapa["estado"])
            if mapa["estado"]
            else None
        )

        linha_original = (
            row.get(mapa["linha"])
            if mapa["linha"]
            else None
        )

        implementadora_original = (
            row.get(mapa["implementadora"])
            if mapa["implementadora"]
            else None
        )

        valor = (
            row.get(mapa["valor"])
            if mapa["valor"]
            else None
        )

        linha = normalizar_produto(
            linha_original
        )

        implementadora = (
            normalizar_implementadora(
                implementadora_original
            )
        )

        if pd.isna(valor):
            valor = 0

        registros.append({

            "estado": (
                str(estado)
                if estado and not pd.isna(estado)
                else ""
            ),

            "linha": linha,

            "implementadora": implementadora,

            "valor": float(valor)

        })

    return registros
