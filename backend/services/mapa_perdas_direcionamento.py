from __future__ import annotations

import unicodedata
from collections import defaultdict
from typing import Any, Callable


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")


def _texto(item: dict[str, Any], *campos: str) -> str:
    for campo in campos:
        valor = str(item.get(campo) or "").strip()
        if valor:
            return valor
    return ""


def direcionar_perda_dominante(
    perdidos: list[dict[str, Any]],
    motivo_dominante: str | None,
    quantidade_fn: Callable[[dict[str, Any], int], int],
    linha_fn: Callable[[dict[str, Any]], str],
    limite: int = 5,
) -> dict[str, Any]:
    """Transforma uma causa de perda em alvo comercial auditável por cliente e responsável."""
    if not motivo_dominante:
        return {"motivo": None, "alvos": [], "texto": ""}

    alvo_fold = _fold(motivo_dominante)
    agrupados: dict[tuple[str, str], dict[str, Any]] = {}

    for item in perdidos:
        motivo = _texto(item, "motivo")
        if _fold(motivo) != alvo_fold:
            continue

        cliente = _texto(item, "cliente", "empresa", "transportadora") or "Cliente não identificado"
        responsavel = _texto(
            item,
            "responsavel",
            "responsável",
            "representante_atual",
            "representante_original",
            "vendedor",
            "consultor",
        ) or "Responsável não informado"
        chave = (_fold(responsavel), _fold(cliente))
        if chave not in agrupados:
            agrupados[chave] = {
                "responsavel": responsavel,
                "cliente": cliente,
                "unidades": 0,
                "ocorrencias": 0,
                "linhas": defaultdict(int),
            }
        grupo = agrupados[chave]
        quantidade = quantidade_fn(item, 1)
        grupo["unidades"] += quantidade
        grupo["ocorrencias"] += 1
        grupo["linhas"][linha_fn(item)] += quantidade

    alvos: list[dict[str, Any]] = []
    for grupo in agrupados.values():
        linhas = sorted(grupo.pop("linhas").items(), key=lambda par: (-par[1], par[0]))
        grupo["linha_principal"] = linhas[0][0] if linhas else "Não classificado"
        alvos.append(grupo)

    alvos.sort(key=lambda item: (-int(item["unidades"]), str(item["responsavel"]), str(item["cliente"])))
    alvos = alvos[: max(1, limite)]

    partes = []
    for item in alvos:
        partes.append(
            f'{item["responsavel"]} → {item["cliente"]} '
            f'({item["unidades"]} un.; {item["linha_principal"]})'
        )
    texto = "Prioridade por responsável e cliente: " + "; ".join(partes) + "." if partes else ""
    return {"motivo": motivo_dominante, "alvos": alvos, "texto": texto}
