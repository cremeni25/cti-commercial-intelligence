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


def direcionar_registros(
    registros: list[dict[str, Any]],
    quantidade_fn: Callable[[dict[str, Any], int], int],
    linha_fn: Callable[[dict[str, Any]], str],
    limite: int = 5,
    responsavel_padrao: str | None = None,
    rotulo: str = "Quem deve agir / para quem",
) -> dict[str, Any]:
    """Agrupa evidências por responsável + cliente sem misturar cliente, ocorrência e unidade."""
    agrupados: dict[tuple[str, str], dict[str, Any]] = {}

    for item in registros:
        cliente = _texto(item, "cliente", "empresa", "transportadora") or "Cliente não identificado"
        responsavel = responsavel_padrao or _texto(
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
    partes = [
        f'{item["responsavel"]} → {item["cliente"]} '
        f'({item["unidades"]} un.; {item["ocorrencias"]} ocorrência(s); {item["linha_principal"]})'
        for item in alvos
    ]
    texto = f"{rotulo}: " + "; ".join(partes) + "." if partes else ""
    return {"alvos": alvos, "texto": texto}


def direcionar_perda_dominante(
    perdidos: list[dict[str, Any]],
    motivo_dominante: str | None,
    quantidade_fn: Callable[[dict[str, Any], int], int],
    linha_fn: Callable[[dict[str, Any]], str],
    limite: int = 5,
) -> dict[str, Any]:
    """Transforma a causa dominante de perda em alvo comercial auditável."""
    if not motivo_dominante:
        return {"motivo": None, "alvos": [], "texto": ""}

    alvo_fold = _fold(motivo_dominante)
    filtrados = [item for item in perdidos if _fold(_texto(item, "motivo")) == alvo_fold]
    direcionamento = direcionar_registros(
        filtrados,
        quantidade_fn,
        linha_fn,
        limite=limite,
        rotulo="Quem deve agir / para quem",
    )
    return {
        "motivo": motivo_dominante,
        "alvos": direcionamento["alvos"],
        "texto": direcionamento["texto"],
    }
