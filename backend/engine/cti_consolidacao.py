# cti_consolidacao.py — ETAPA 13.1.1
# Motor Oficial de Consolidação do CTI

from collections import defaultdict

from engine.cti_id_inteligente import gerar_id_cliente
from core.cti_taxonomy import normalizar_implementadora


MARCAS_PRIORITARIAS = [
    "CARRIER",
    "THERMO KING",
    "RODOFRIO",
    "FRIGOKING",
    "THERMOSTAR"
]


def classificar_marca(marca: str) -> str:

    if not marca:
        return "OUTROS"

    marca = str(marca).upper()

    for m in MARCAS_PRIORITARIAS:
        if m in marca:
            return m

    return "OUTROS"

def obter_campo(row, *campos):

    for campo in campos:

        valor = row.get(campo)

        if valor not in (None, "", "nan"):

            return valor

    return None


def obter_valor(row):

    valor = obter_campo(
        row,
        "valor",
        "VALOR",
        "VALOR - CARRIER",
        "VALOR - CONCORRÊNCIA"
    )

    try:
        return float(valor or 0)
    except:
        return 0.0


def consolidar_dados(registros: list) -> dict:
    """
    Motor Oficial de Consolidação CTI

    Consolida atualmente:

    • Clientes
    • Implementadoras
    • Estados
    • DDD
    • Marcas

    (ETAPA 13 em evolução)
    """

    clientes = {}

    implementadoras = {}

    por_estado = defaultdict(float)
    por_ddd = defaultdict(float)
    por_marca = defaultdict(float)

    total_geral = 0

    # ==========================================================
    # ENTIDADE MESTRE DO CTI
    # Histórico por veículo (CHASSI + PLACA)
    # ==========================================================

    veiculos = {}
    
    for row in registros:

        valor = obter_valor(row)

        estado = obter_campo(
            row,
            "estado",
            "ESTADO"
        ) or "UNKNOWN"

        ddd = str(
            obter_campo(
            row,
            "ddd",
            "DDD"
        ) or "00"
)
          
        marca = classificar_marca(
            obter_campo(
            row,
            "marca",
            "MARCA",
            "FABRICANTE EQUIPAMENTO"
        )
)

        id_cliente = gerar_id_cliente(row)

        id_operacional = (
            obter_campo(
                row,
                "id_operacional",
                "ID_OPERACIONAL"
            )
            or (
                f"{obter_campo(row,'chassi','CHASSI')}_"
                f"{obter_campo(row,'placa','PLACA')}"
            )
        )

        if id_operacional not in veiculos:

            veiculos[id_operacional] = {

                "id_operacional": id_operacional,

                "placa": obter_campo(
                    row,
                    "placa",
                    "PLACA"
                ),

                "chassi": obter_campo(
                    row,
                    "chassi",
                    "CHASSI"
                ),

                "clientes": set(),

                "implementadoras": set(),

                "estados": set(),

                "ddd": set(),

                "marcas": set(),

                "linhas": defaultdict(int),

                "valor_total": 0.0,

                "ocorrencias": 0

            }

        veiculo = veiculos[id_operacional]

        veiculo["clientes"].add(id_cliente)

        veiculo["estados"].add(estado)

        veiculo["ddd"].add(ddd)

        veiculo["marcas"].add(marca)

        veiculo["valor_total"] += valor

        veiculo["ocorrencias"] += 1

        total_geral += valor

        # ======================================================
        # CLIENTE
        # ======================================================

        if id_cliente not in clientes:

            clientes[id_cliente] = {

                "cliente": row.get("cliente"),

                "estado": estado,

                "ddd": ddd,

                "total": 0

            }

        clientes[id_cliente]["total"] += valor

        # ======================================================
        # IMPLEMENTADORA (NOVA CONSOLIDAÇÃO)
        # ======================================================

        implementadora = normalizar_implementadora(

            obter_campo(

                row,

                "implementadora",

                "implementador",

                "IMPLEMENTADORA"

            ) or ""

        )

        if implementadora:

            if implementadora not in implementadoras:

                implementadoras[implementadora] = {

                    "nome": implementadora,

                    "negocios": 0,

                    "clientes": set(),

                    "placas": set(),

                    "chassis": set(),

                    "estados": set(),

                    "ddd": set(),

                    "linhas": defaultdict(int),

                    "valor_total": 0.0

                }

            imp = implementadoras[implementadora]

            imp["negocios"] += 1

            imp["valor_total"] += valor

            imp["clientes"].add(id_cliente)

            placa = obter_campo(
                row,
                "placa",
                "PLACA"
            )

            if placa:

                imp["placas"].add(
                    str(placa).upper()
                )

            chassi = obter_campo(
                row,
                "chassi",
                "CHASSI"
            )

            if chassi:

                imp["chassis"].add(
                    str(chassi).upper()
                )

            if estado:
                imp["estados"].add(estado)

            if ddd:
                imp["ddd"].add(ddd)

            linha = obter_campo(

                row,

                "linha",

                "LINHA",

                "LINHA DE PRODUTO",

                "MODELO DE PRODUTO",

                "MODELO DE PRODUTO - CARRIER"

            )

            if not linha:
                linha = "OUTROS"

            imp["linhas"][linha] += 1

            veiculo["implementadoras"].add(
                implementadora
            )

            veiculo["linhas"][linha] += 1

# ======================================================
# AGREGAÇÕES GERAIS
# ======================================================

        por_estado[estado] += valor

        por_ddd[ddd] += valor

        por_marca[marca] += valor

    # ==========================================================
    # IMPLEMENTADORAS CONSOLIDADAS
    # ==========================================================

    implementadoras_consolidadas = {}

    for nome, dados in implementadoras.items():

        implementadoras_consolidadas[nome] = {

            "nome": nome,

            "negocios": dados["negocios"],

            "clientes": len(dados["clientes"]),

            "placas": len(dados["placas"]),

            "chassis": len(dados["chassis"]),

            "valor_total": round(
                dados["valor_total"],
                2
            ),

            "estados": sorted(
                list(dados["estados"])
            ),

            "ddd": sorted(
                list(dados["ddd"])
            ),

            "linhas": dict(
                dados["linhas"]
            )

        }

    # ==========================================================
    # VEÍCULOS CONSOLIDADOS
    # ==========================================================

    veiculos_consolidados = {}

    for id_operacional, dados in veiculos.items():

        veiculos_consolidados[id_operacional] = {

            "id_operacional": id_operacional,

            "placa": dados["placa"],

            "chassi": dados["chassi"],

            "clientes": len(dados["clientes"]),

            "implementadoras": len(
                dados["implementadoras"]
            ),

            "ocorrencias": dados["ocorrencias"],

            "valor_total": round(
                dados["valor_total"],
                2
            ),

            "estados": sorted(
                list(dados["estados"])
            ),

            "ddd": sorted(
                list(dados["ddd"])
            ),

            "marcas": sorted(
                list(dados["marcas"])
            ),

            "linhas": dict(
                dados["linhas"]
            )

        }

    # ==========================================================
    # MARKET SHARE
    # ==========================================================

    share_marca = {}

    for dados in veiculos.values():

        for marca in dados["marcas"]:

            share_marca.setdefault(
                marca,
                0
            )

            share_marca[marca] += 1

    total_marcas = sum(
        share_marca.values()
    )

    if total_marcas:

        for marca in list(
            share_marca.keys()
        ):

            share_marca[marca] = round(

                share_marca[marca]
                / total_marcas
                * 100,

                2

            )

    # ==========================================================
    # SHARE POR DDD (BASE VEÍCULO)
    # ==========================================================

    share_ddd = {}

    for dados in veiculos.values():

        for ddd in dados["ddd"]:

            share_ddd.setdefault(
                ddd,
                0
            )

            share_ddd[ddd] += 1

    total_ddd = sum(
        share_ddd.values()
    )

    if total_ddd:

        for ddd in list(
            share_ddd.keys()
        ):

            share_ddd[ddd] = round(

                share_ddd[ddd]
                / total_ddd
                * 100,

                2

            )

    # ==========================================================
    # RESUMO OFICIAL
    # ==========================================================
    ticket_medio = (
        total_geral / len(registros)
        if registros else 0
    )

    resumo = {
        "total_registros": len(registros),
        "total_clientes": len(
            {
                cliente
                for veiculo in veiculos.values()
                for cliente in veiculo["clientes"]
            }
        ),
        
        "total_implementadoras": len(
            {
                implementadora
                for veiculo in veiculos.values()
                for implementadora
                in veiculo["implementadoras"]
            }
        ),
        "total_estados": len(por_estado),
        "ticket_medio": round(ticket_medio, 2),
        "valor_total": round(total_geral, 2),

        "total_veiculos": len(
            veiculos
        ),

        "total_chassis": len(
            {
                dados["chassi"]
                for dados in veiculos.values()
                if dados["chassi"]
            }
        ),

        "total_placas": len(
            {
                dados["placa"]
                for dados in veiculos.values()
                if dados["placa"]
            }
        ),
    }

    # ==========================================================
    # RETORNO
    # ==========================================================
    return {
        "total_geral": round(total_geral, 2),
        "clientes": clientes,
        "veiculos": veiculos_consolidados,
        "implementadoras": implementadoras_consolidadas,
        "por_estado": dict(por_estado),
        "por_ddd": dict(por_ddd),
        "por_marca": dict(por_marca),
        "share_marca": share_marca,
        "share_ddd": share_ddd,
        "resumo": resumo,
    }