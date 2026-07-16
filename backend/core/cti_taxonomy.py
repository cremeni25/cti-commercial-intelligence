from core.entity_normalizer import normalizar_entidade

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

    # --------------------------------------------------------
    # RANDON
    # --------------------------------------------------------

    "RANDON": "RANDON",
    "RANDON IMPLEMENTOS": "RANDON",

    # --------------------------------------------------------
    # IBIPORÃ
    # --------------------------------------------------------

    "IBIPORA": "IBIPORÃ",
    "IBIPORÃ": "IBIPORÃ",

    # --------------------------------------------------------
    # SULBRASIL
    # --------------------------------------------------------

    "SULBRASIL": "SULBRASIL",
    "SUL BRASIL": "SULBRASIL",

    # --------------------------------------------------------
    # MERCOSUL
    # --------------------------------------------------------

    "MERCOSUL": "MERCOSUL",
    "MERCOSUL IMPLEMENTOS RODOVIÁRIOS LTDA.": "MERCOSUL",

    # --------------------------------------------------------
    # NIJU
    # --------------------------------------------------------

    "NIJU": "NIJU",

    # --------------------------------------------------------
    # FACCHINI
    # --------------------------------------------------------

    "FACCHINI": "FACCHINI",

    # --------------------------------------------------------
    # FIBRASIL
    # --------------------------------------------------------

    "FIBRASIL": "FIBRASIL",

    # --------------------------------------------------------
    # FIBRA WEST
    # --------------------------------------------------------

    "FIBRA WEST": "FIBRA WEST",
    "FIBRA WEST COMÉRCIO DE CARROCERIAS LTDA": "FIBRA WEST",

    # --------------------------------------------------------
    # FIBRA VEST
    # --------------------------------------------------------

    "FIBRA VEST": "FIBRA VEST",

    # --------------------------------------------------------
    # FORZA
    # --------------------------------------------------------

    "FORZA": "FORZA",
    "FORZA FABRICACAO": "FORZA",
    "FORZA FABRICAÇÃO E MANUTENÇÃO DE CAMARAS FRIAS LTDA": "FORZA",

    # --------------------------------------------------------
    # FRIGOFUR
    # --------------------------------------------------------

    "FRIGOFUR": "FRIGOFUR",
    "FRIGOFUR INDÚSTRIA E COMERCIO": "FRIGOFUR",

    # --------------------------------------------------------
    # FURGOBEN
    # --------------------------------------------------------

    "FURGOBEN EQUIP. RODOVIÁRIOS LTDA.": "FURGOBEN",

    # --------------------------------------------------------
    # HC
    # --------------------------------------------------------

    "HC": "HC",

    # --------------------------------------------------------
    # HIDRAUCAM
    # --------------------------------------------------------

    "HIDRAUCAM": "HIDRAUCAM",
    "HIDRAUCAM INDÚSTRIA COMÉRCIO E MANUTENÇÃO": "HIDRAUCAM",

    # --------------------------------------------------------
    # HIDROAUM
    # --------------------------------------------------------

    "HIDROAUM": "HIDROAUM",
    "HIDROAUM INDUSTRIA COMERCIO E MANUTENCAO": "HIDROAUM",

    # --------------------------------------------------------
    # HIGH FLEX
    # --------------------------------------------------------

    "HIGH FLEX": "HIGH FLEX",
    "HIGH FLEX INDUSTRIA": "HIGH FLEX",
    "HIGH FLEX INDÚSTRIA": "HIGH FLEX",
    "HIGH FLEX INDUSTRIA E COMERCIO": "HIGH FLEX",
    "HIGH FLEX INDÚSTRIA E COMÉRCIO": "HIGH FLEX",
    "HIGH FLEX INDÚSTRIA E COMÉRCIO E COMÉRCIO DE IMPLEMENTOS EIRELI - EPP": "HIGH FLEX",

    # --------------------------------------------------------
    # ICEBOX
    # --------------------------------------------------------

    "ICEBOX INDÚSTRIA COMÉRCIO": "ICEBOX",

    # --------------------------------------------------------
    # JOVEMOL
    # --------------------------------------------------------

    "JOVEMOL": "JOVEMOL",

    # --------------------------------------------------------
    # JSO
    # --------------------------------------------------------

    "JSO TRUCK": "JSO TRUCK",

    # --------------------------------------------------------
    # MARKSELL
    # --------------------------------------------------------

    "MARKSELL": "MARKSELL",

    # --------------------------------------------------------
    # PALÁCIO
    # --------------------------------------------------------

    "PALACIO DO ISOLAMENTO": "PALACIO DO ISOLAMENTO",
    "PALACIO DO ISOLAMENTO E REFRIGERAÇÃO": "PALACIO DO ISOLAMENTO",

    # --------------------------------------------------------
    # PAVAN
    # --------------------------------------------------------

    "PAVAN": "PAVAN",
    "PAVAN INDUSTRIA DE CAMARAS": "PAVAN",
    "PAVAN INDÚSTRIA DE CAMARAS": "PAVAN",
    "PAVAN INDUSTRIA DE CÂMARAS": "PAVAN",
    "PAVAN INDÚSTRIA DE CÂMARAS": "PAVAN",
    "PAVAN INDÚSTRIA DE CAMÂRAS": "PAVAN",

    # --------------------------------------------------------
    # SHARK
    # --------------------------------------------------------

    "SHARK": "SHARK",

    # --------------------------------------------------------
    # SP4
    # --------------------------------------------------------

    "SP4 INDUSTRIA DE IMPLEMENTOS RODOVIÁRIOS LTDA": "SP4",

    # --------------------------------------------------------
    # TITON
    # --------------------------------------------------------

    "TITON E CIA LTDA": "TITON",

    # --------------------------------------------------------
    # TRANSPORTES PAVAN
    # --------------------------------------------------------

    "TRANSPORTES IRMÃOS PAVAN LTDA": "TRANSPORTES IRMÃOS PAVAN",

    # --------------------------------------------------------
    # VIA BRAZIL
    # --------------------------------------------------------

    "VIA BRAZIL VEÍCULOS ESPECIAIS EQUIPAMENTOS LTDA": "VIA BRAZIL",

    # --------------------------------------------------------
    # ENOVA
    # --------------------------------------------------------

    "ENOVA": "ENOVA",

    # --------------------------------------------------------
    # COMERCIO INDUSTRIA
    # --------------------------------------------------------

    "COMERCIO INDUSTRIA": "COMERCIO INDUSTRIA",

    # --------------------------------------------------------
    # LABONIA
    # --------------------------------------------------------

    "LABONIA": "LABONIA"
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

    produto = normalizar_entidade(produto)

    if produto in PRODUTOS:
        return PRODUTOS[produto]

    for original, oficial in PRODUTOS.items():

        if normalizar_entidade(original) == produto:
            return oficial

    return produto


def normalizar_implementadora(nome):

    if not nome:
        return None

    chave = normalizar_entidade(nome)

    if chave in IMPLEMENTADORAS:
        return IMPLEMENTADORAS[chave]

    for original, oficial in IMPLEMENTADORAS.items():

        if normalizar_entidade(original) == chave:
            return oficial

    return chave



def aliases_implementadora(nome_oficial):

    oficial = normalizar_implementadora(nome_oficial)

    if not oficial:
        return []

    aliases = {oficial}

    for alias, destino in IMPLEMENTADORAS.items():

        if destino == oficial:
            aliases.add(alias)

    return sorted(aliases)


def todas_implementadoras_oficiais():

    return sorted(set(IMPLEMENTADORAS.values()))


def mapa_aliases_implementadoras():

    return {
        oficial: aliases_implementadora(oficial)
        for oficial in todas_implementadoras_oficiais()
    }

def fabricante_valido(nome):

    if not nome:
        return False

    nome = normalizar_entidade(nome)

    for fabricante in FABRICANTES_EQUIPAMENTO:

        if normalizar_entidade(fabricante) in nome:
            return True

    return False


def status_valido(status):

    if not status:
        return False

    return (
        str(status).upper().strip()
        in STATUS_OPERACIONAIS
    )


def cliente_lixo(cliente):

    if not cliente:
        return True

    return (
        str(cliente).upper().strip()
        in LIXO_OPERACIONAL
    )

# ============================================================
# CONSOLIDAÇÕES CENTRAIS
# ============================================================

def consolidar_cliente(cliente):

    return normalizar_entidade(cliente)


def consolidar_transportadora(nome):

    return normalizar_entidade(nome)


def consolidar_cidade(nome):

    return normalizar_entidade(nome)
