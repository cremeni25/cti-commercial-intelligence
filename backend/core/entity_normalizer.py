# ============================================================
# CTI - MOTOR INTELIGENTE DE CONSOLIDAÇÃO DE ENTIDADES
# Arquivo: backend/core/entity_normalizer.py
# ============================================================

import re
import unicodedata

# ============================================================
# PALAVRAS DESCARTÁVEIS
# ============================================================

STOPWORDS = {

    "LTDA",
    "EIRELI",
    "ME",
    "EPP",
    "S/A",
    "SA",

    "INDUSTRIA",
    "INDÚSTRIA",

    "COMERCIO",
    "COMÉRCIO",

    "FABRICACAO",
    "FABRICAÇÃO",

    "IMPLEMENTOS",
    "IMPLEMENTO",

    "RODOVIARIOS",
    "RODOVIÁRIOS",

    "DO",
    "DA",
    "DE",
    "DOS",
    "DAS",
    "E",

    "TRANSPORTES",
    "TRANSPORTE",

    "VEICULOS",
    "VEÍCULOS",

    "ESPECIAIS",

    "EQUIPAMENTOS",
    "EQUIPAMENTO",

    "IND",
    "IND.",

    "COM",
    "COM.",

    "CIA",
    "CIA.",

    "MATRIZ",
    "FILIAL"

}

# ============================================================
# REMOVE ACENTOS
# ============================================================

def remover_acentos(texto: str) -> str:

    return "".join(

        c

        for c in unicodedata.normalize(
            "NFKD",
            texto
        )

        if not unicodedata.combining(c)

    )


# ============================================================
# LIMPEZA GERAL
# ============================================================

def limpar_texto(texto: str) -> str:

    if not texto:
        return ""

    texto = str(texto).upper()

    texto = remover_acentos(texto)

    texto = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    return texto


# ============================================================
# TOKENIZAÇÃO
# ============================================================

def tokenizar(texto: str) -> list[str]:

    texto = limpar_texto(texto)

    tokens = []

    for token in texto.split():

        if token not in STOPWORDS:

            tokens.append(token)

    return tokens


# ============================================================
# ASSINATURA SEMÂNTICA
# ============================================================

def assinatura(texto: str) -> str:

    tokens = tokenizar(texto)

    tokens = sorted(set(tokens))

    return " ".join(tokens)


# ============================================================
# NORMALIZADOR CENTRAL
# ============================================================

def normalizar_entidade(texto: str) -> str:

    if not texto:
        return ""

    return assinatura(texto)


# ============================================================
# COMPARAÇÃO DE ENTIDADES
# ============================================================

def sao_mesma_entidade(
    entidade_a: str,
    entidade_b: str,
) -> bool:

    return (

        normalizar_entidade(entidade_a)

        ==

        normalizar_entidade(entidade_b)

    )


# ============================================================
# NORMALIZAÇÃO EM LOTE
# ============================================================

def normalizar_lista(lista: list[str]) -> list[str]:

    resultado = []

    for item in lista:

        resultado.append(
            normalizar_entidade(item)
        )

    return resultado


# ============================================================
# CONSOLIDAÇÃO DE ENTIDADES
# ============================================================

def consolidar_entidades(lista: list[str]) -> list[str]:

    entidades = {

        normalizar_entidade(item)

        for item in lista

        if item

    }

    return sorted(entidades)


# ============================================================
# CONTAGEM DE ENTIDADES ÚNICAS
# ============================================================

def quantidade_entidades(lista: list[str]) -> int:

    return len(

        consolidar_entidades(lista)

    )