import re

def extrair_texto_generico(df):
    linhas = []

    for _, row in df.iterrows():
        linha = " ".join([str(v) for v in row.values if str(v) != "nan"])
        linhas.append(linha)

    return linhas


def interpretar_linha(texto, origem="desconhecido"):
    texto_lower = texto.lower()

    # valor
    valor_match = re.search(r'(\d+[.,]?\d*)', texto.replace(".", "").replace(",", "."))
    valor = float(valor_match.group(1)) if valor_match else 0

    # cliente (heurística simples)
    cliente = ""
    if "ltda" in texto_lower or "sa" in texto_lower:
        cliente = texto

    # data (ano simples)
    data_match = re.search(r'(20\d{2})', texto)
    data = data_match.group(1) if data_match else ""

    return {
        "cliente": cliente,
        "valor": valor,
        "data": data,
        "texto_original": texto,
        "origem": origem
    }


def processar_conteudo(df, origem="desconhecido"):
    linhas = extrair_texto_generico(df)

    registros = []

    for linha in linhas:
        registro = interpretar_linha(linha, origem)

        # NÃO filtrar agressivamente
        registros.append(registro)

    return registros
