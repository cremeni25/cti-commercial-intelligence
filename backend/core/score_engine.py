from collections import defaultdict
from core.cti_taxonomy import (
    normalizar_produto,
    normalizar_implementadora,
    fabricante_valido
)


def calcular_score_registro(registro):

    score = 0

    valor = float(registro.get("valor") or 0)

    if valor >= 500000:
        score += 40

    elif valor >= 150000:
        score += 25

    elif valor >= 40000:
        score += 10

    cliente = registro.get("cliente")

    if cliente:
        score += 15

    produto = normalizar_produto(
        registro.get("produto")
    )

    if produto:
        score += 20

    implementadora = normalizar_implementadora(
        registro.get("implementadora")
    )

    if implementadora:
        score += 15

    concorrente = registro.get("concorrente")

    if fabricante_valido(concorrente):
        score += 25

    return score


def consolidar_scores(registros):

    resultado = {
        "score_total": 0,
        "clientes": defaultdict(int),
        "produtos": defaultdict(int),
        "implementadoras": defaultdict(int),
        "concorrentes": defaultdict(int),
        "estados": defaultdict(int)
    }

    for r in registros:

        score = calcular_score_registro(r)

        resultado["score_total"] += score

        cliente = r.get("cliente")
        produto = normalizar_produto(
            r.get("produto")
        )

        implementadora = normalizar_implementadora(
            r.get("implementadora")
        )

        concorrente = r.get("concorrente")
        estado = r.get("estado")

        if cliente:
            resultado["clientes"][cliente] += score

        if produto:
            resultado["produtos"][produto] += score

        if implementadora:
            resultado["implementadoras"][implementadora] += score

        if concorrente:
            resultado["concorrentes"][concorrente] += score

        if estado:
            resultado["estados"][estado] += score

    return resultado