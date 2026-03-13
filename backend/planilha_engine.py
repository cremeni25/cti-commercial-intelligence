import pandas as pd
from io import BytesIO


def normalizar_colunas(df):

    df.columns = [
        str(c).strip().upper().replace("Ç","C").replace("Ã","A")
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

    mapa["fabricante"] = detectar_coluna(df, [
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


def processar_planilha_universal(contents):

    df = pd.read_excel(BytesIO(contents))

    df = normalizar_colunas(df)

    mapa = detectar_mapeamento(df)

    registros = []

    for _, row in df.iterrows():

        estado = row.get(mapa["estado"]) if mapa["estado"] else None
        linha = row.get(mapa["linha"]) if mapa["linha"] else None
        fabricante = row.get(mapa["fabricante"]) if mapa["fabricante"] else None
        valor = row.get(mapa["valor"]) if mapa["valor"] else None

        if pd.isna(valor):
            valor = 0

        registros.append({

            "estado": str(estado) if estado and not pd.isna(estado) else "",
            "linha": str(linha) if linha and not pd.isna(linha) else "",
            "implementador": str(fabricante) if fabricante and not pd.isna(fabricante) else "",
            "valor": float(valor)

        })

    return registros
