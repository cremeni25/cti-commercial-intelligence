import pandas as pd
import re

# ================================
# NORMALIZAÇÃO TEXTO
# ================================
def normalizar(txt):
    return re.sub(r'[^a-z0-9]', '', str(txt).lower())


# ================================
# DICIONÁRIO INTELIGENTE
# ================================
DICIONARIO = {
    "cliente": ["cliente", "nome", "razao", "fantasia", "comprador"],
    "cnpj": ["cnpj", "cpf", "documento"],
    "data": ["data", "dt", "emissao", "venda"],
    "valor": ["valor", "total", "preco", "r$", "faturamento"],
    "cidade": ["cidade", "municipio"],
    "estado": ["estado", "uf"],
    "produto": ["produto", "item", "descricao"]
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

                # MELHORIA AQUI
                if s in col_norm or col_norm in s:
                    mapeamento[col] = campo
                    break

            if col in mapeamento:
                break

    print("COLUNAS IDENTIFICADAS:", df.columns.tolist())
    print("MAPEAMENTO GERADO:", mapeamento)

    return mapeamento

# ================================
# NORMALIZADOR FINAL
# ================================
def normalizar_dataframe(df, origem):

    mapeamento = mapear_colunas(df)

    df = df.rename(columns=mapeamento)

    registros = []

    for _, row in df.iterrows():

        registro = {
            "cliente": str(row.get("cliente") or ""),
            "cnpj": re.sub(r"\D", "", str(row.get("cnpj") or "")),
            "data": str(row.get("data") or ""),
            "valor": float(row.get("valor") or 0),
            "cidade": str(row.get("cidade") or ""),
            "estado": str(row.get("estado") or ""),
            "produto": str(row.get("produto") or ""),
            "origem": origem,
            "extra": row.to_dict()
        }

        # REGRA MÍNIMA
        if not registro["cliente"] and registro["valor"] == 0:
            continue

        registros.append(registro)

    return registros
