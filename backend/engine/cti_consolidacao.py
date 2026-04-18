# cti_consolidacao.py — versão completa e final

from collections import defaultdict
from engine.cti_id_inteligente import gerar_id_cliente


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

    marca = marca.upper()

    for m in MARCAS_PRIORITARIAS:
        if m in marca:
            return m

    return "OUTROS"


def consolidar_dados(registros: list) -> dict:
    """
    Consolida dados em múltiplas dimensões:
    - Cliente
    - Estado
    - DDD
    - Marca
    """

    clientes = {}
    por_estado = defaultdict(float)
    por_ddd = defaultdict(float)
    por_marca = defaultdict(float)

    total_geral = 0

    for row in registros:

        valor = float(row.get("valor", 0) or 0)
        estado = row.get("estado", "UNKNOWN")
        ddd = str(row.get("ddd", "00"))
        marca = classificar_marca(row.get("marca"))

        id_cliente = gerar_id_cliente(row)

        total_geral += valor

        # CLIENTE
        if id_cliente not in clientes:
            clientes[id_cliente] = {
                "cliente": row.get("cliente"),
                "estado": estado,
                "ddd": ddd,
                "total": 0
            }

        clientes[id_cliente]["total"] += valor

        # AGREGAÇÕES
        por_estado[estado] += valor
        por_ddd[ddd] += valor
        por_marca[marca] += valor

    # MARKET SHARE
    share_marca = {
        marca: (valor / total_geral * 100 if total_geral else 0)
        for marca, valor in por_marca.items()
    }

    share_ddd = {
        ddd: (valor / total_geral * 100 if total_geral else 0)
        for ddd, valor in por_ddd.items()
    }

    return {
        "total_geral": total_geral,
        "clientes": clientes,
        "por_estado": dict(por_estado),
        "por_ddd": dict(por_ddd),
        "por_marca": dict(por_marca),
        "share_marca": share_marca,
        "share_ddd": share_ddd
    }
