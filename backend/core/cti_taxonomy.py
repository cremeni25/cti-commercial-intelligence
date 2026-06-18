# ============================================================
# CTI - TAXONOMIA CENTRAL
# Núcleo semântico oficial do sistema
# ============================================================


# ============================================================
# PRODUTOS OFICIAIS
# ============================================================

PRODUTOS = {

    "TR": "TR",

    "TRAILER": "TR",

    "SEMI REBOQUE": "TR",

    "SEMIREBOQUE": "TR",


    "DT": "DT",

    "DIESEL": "DT",

    "DIESEL TRUCK": "DT",


    "DD": "DD",

    "DIRECT": "DD",

    "DIRECT DRIVE": "DD"
}


# ============================================================
# IMPLEMENTADORAS OFICIAIS
# ============================================================

IMPLEMENTADORAS = {

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


# ============================================================
# FABRICANTES EQUIPAMENTO
# ============================================================

FABRICANTES_EQUIPAMENTO = [

    "CARRIER",

    "THERMO KING",

    "THERMOKING",

    "FRIGOKING",

    "THERMOSTAR",

    "RODOFRIO",

    "THERMOFLEX"
]


# ============================================================
# STATUS OPERACIONAIS
# ============================================================

STATUS_OPERACIONAIS = [

    "APROVADO",

    "PERDIDO",

    "GANHO",

    "EM NEGOCIACAO",

    "SEM SOLUCAO TECNICA"
]


# ============================================================
# LIXO OPERACIONAL
# ============================================================

LIXO_OPERACIONAL = [

    "UNIDADES",

    "SUDESTE",

    "SUL",

    "NORTE",

    "NORDESTE",

    "SP",

    "BRASIL",

    "FILIAL",

    "MATRIZ"
]


# ============================================================
# NORMALIZADORES CENTRAIS
# ============================================================

def normalizar_produto(produto):

    if not produto:
        return None

    p = str(produto).upper().strip()

    return PRODUTOS.get(p)


def normalizar_implementadora(nome):

    if not nome:
        return None

    n = str(nome).upper().strip()

    return IMPLEMENTADORAS.get(
        n,
        n
    )


def fabricante_valido(nome):

    if not nome:
        return False

    n = str(nome).upper().strip()

    return any(
        f in n
        for f in FABRICANTES_EQUIPAMENTO
    )


def status_valido(status):

    if not status:
        return False

    s = str(status).upper().strip()

    return s in STATUS_OPERACIONAIS


def cliente_lixo(cliente):

    if not cliente:
        return True

    c = str(cliente).upper().strip()

    return c in LIXO_OPERACIONAL

