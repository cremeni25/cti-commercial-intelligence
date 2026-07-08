import pandas as pd
import re


# ================================
# NORMALIZAÇÃO TEXTO
# ================================
def normalizar(txt):

    return re.sub(
        r'[^a-z0-9]',
        '',
        str(txt).lower()
    )


# ================================
# DICIONÁRIO INTELIGENTE
# ================================
DICIONARIO = {

    "cliente": [
        "cliente",
        "nome",
        "razao",
        "fantasia",
        "comprador"
    ],

    "cnpj": [
        "cnpj",
        "cpf",
        "documento"
    ],

    "data": [
        "data",
        "dt",
        "emissao",
        "venda"
    ],

    "valor": [
        "valor",
        "total",
        "preco",
        "r$",
        "faturamento"
    ],

    "cidade": [
        "cidade",
        "municipio"
    ],

    "estado": [
        "estado",
        "uf"
    ],

    "produto": [
        "produto",
        "item",
        "descricao"
    ]
}


# ================================
# MAPEAMENTO INTELIGENTE
# ================================
def mapear_colunas(df):

    mapeamento = {}

    for col in df.columns:

        col_norm = normalizar(col)

        for campo, sinonimos in DICIONARIO.items():

            for s in sinonimos:

                if s in col_norm or col_norm in s:

                    mapeamento[col] = campo
                    break

            if col in mapeamento:
                break

    print(
        "COLUNAS IDENTIFICADAS:",
        df.columns.tolist()
    )

    print(
        "MAPEAMENTO GERADO:",
        mapeamento
    )

    return mapeamento


# ================================
# NORMALIZADOR FINAL
# ================================
def normalizar_dataframe(df, origem):

    mapeamento = mapear_colunas(df)

    df = df.rename(
        columns=mapeamento
    )

    registros = []

    for _, row in df.iterrows():

        valor = float(
            row.get("valor") or 0
        )

        registro = {

            "cliente": str(
                row.get("cliente") or ""
            ),

            "cnpj": re.sub(
                r"\D",
                "",
                str(
                    row.get("cnpj") or ""
                )
            ),

            "data": str(
                row.get("data") or ""
            ),

            "valor": valor,

            "cidade": str(
                row.get("cidade") or ""
            ),

            "estado": str(
                row.get("estado") or ""
            ),

            "produto": str(
                row.get("produto") or ""
            ),

            "produto_normalizado": normalizar(
                str(
                    row.get("produto") or ""
                )
            ),

            "origem": origem,

            "score_inicial": 0,

            "classificacao": "",

            "extra": row.to_dict()
        }

        # ================================
        # REGRA MÍNIMA
        # ================================
        if (
            not registro["cliente"]
            and registro["valor"] == 0
        ):
            continue

        # ================================
        # SCORE OPERACIONAL
        # ================================
        if valor > 500000:

            registro["score_inicial"] += 40

        elif valor > 150000:

            registro["score_inicial"] += 25

        elif valor > 50000:

            registro["score_inicial"] += 10

        # ================================
        # CLASSIFICAÇÃO
        # ================================
        if registro["score_inicial"] >= 40:

            registro["classificacao"] = (
                "ESTRATEGICO"
            )

        elif registro["score_inicial"] >= 25:

            registro["classificacao"] = (
                "ALTO_POTENCIAL"
            )

        else:

            registro["classificacao"] = (
                "OPERACIONAL"
            )

        registros.append(registro)

    return registros

