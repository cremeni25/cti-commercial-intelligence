from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

from services.operational_filters import data_registro
from services.product_line_classifier import classificar_linha

IMPLEMENTADORAS_FORA_ESCOPO = ("FIBRA WEST", "HIGH FLEX", "PLANALTO")
NOMES_SEGMENTOS = {"TR": "Trailer", "DT": "Diesel Truck", "DD": "Direct Drive"}
MESES = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}


def _normalizar(valor: Any) -> str:
    texto = str(valor or "").strip().upper()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", texto).strip()


def implementadora_fora_escopo(registro: dict[str, Any]) -> str | None:
    nome = _normalizar(registro.get("implementadora") or registro.get("implementador"))
    if not nome:
        return None
    if "FIBRA WEST" in nome:
        return "FIBRA WEST"
    if "HIGH FLEX" in nome or "HIFLEX" in nome or "HI FLEX" in nome:
        return "HIGH FLEX"
    if "PLANALTO" in nome:
        return "PLANALTO"
    return None


def filtrar_mercado_real_viena(registros: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """Aplica a regra comercial global sem alterar a fonte bruta auditável.

    Fibra West, High Flex (incluindo aliases HiFlex/Hi Flex) e Planalto
    permanecem disponíveis apenas nas fontes brutas/auditoria, mas nunca
    compõem o universo comercial disputável da Viena.
    """
    return [dict(item) for item in registros if not implementadora_fora_escopo(item)]


def _comparativo_mensal(registros: list[dict[str, Any]], fora: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_por_mes: Counter[int] = Counter()
    fora_por_mes: Counter[int] = Counter()
    for item in registros:
        data = data_registro(item)
        if data and data.year == 2026:
            total_por_mes[data.month] += 1
    for item in fora:
        data = data_registro(item)
        if data and data.year == 2026:
            fora_por_mes[data.month] += 1
    retorno = []
    for mes in range(1, 13):
        total = total_por_mes.get(mes, 0)
        excluido = fora_por_mes.get(mes, 0)
        if not total and not excluido:
            continue
        retorno.append({
            "mes": MESES[mes],
            "competencia": f"2026-{mes:02d}",
            "mercado_total": total,
            "mercado_excluido": excluido,
            "mercado_real": total - excluido,
        })
    return retorno


def _comparativo_segmentos(registros: list[dict[str, Any]], fora: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total: Counter[str] = Counter(classificar_linha(item) or "UNKNOWN" for item in registros)
    excluido: Counter[str] = Counter(classificar_linha(item) or "UNKNOWN" for item in fora)
    retorno = []
    for codigo in ("TR", "DT", "DD"):
        mercado_total = total.get(codigo, 0)
        mercado_excluido = excluido.get(codigo, 0)
        retorno.append({
            "codigo": codigo,
            "segmento": NOMES_SEGMENTOS[codigo],
            "mercado_total": mercado_total,
            "mercado_excluido": mercado_excluido,
            "mercado_real": mercado_total - mercado_excluido,
        })
    return retorno


def particionar_mercado_disputavel(
    registros: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    disputavel: list[dict[str, Any]] = []
    fora: list[dict[str, Any]] = []
    por_implementadora: Counter[str] = Counter()
    por_implementadora_linha: dict[str, Counter[str]] = defaultdict(Counter)
    variantes: dict[str, Counter[str]] = defaultdict(Counter)

    for item in registros:
        registro = dict(item)
        canonico = implementadora_fora_escopo(registro)
        if not canonico:
            disputavel.append(registro)
            continue
        fora.append(registro)
        por_implementadora[canonico] += 1
        por_implementadora_linha[canonico][classificar_linha(registro) or "UNKNOWN"] += 1
        bruto = str(registro.get("implementadora") or registro.get("implementador") or canonico).strip()
        variantes[canonico][bruto or canonico] += 1

    total = len(registros)
    total_fora = len(fora)
    total_disputavel = len(disputavel)
    percentual_fora = round(total_fora / total * 100, 2) if total else 0.0
    percentual_disputavel = round(total_disputavel / total * 100, 2) if total else 0.0

    resumo_implementadoras = []
    for nome in IMPLEMENTADORAS_FORA_ESCOPO:
        por_linha = por_implementadora_linha[nome]
        tr = por_linha.get("TR", 0)
        dt = por_linha.get("DT", 0)
        dd = por_linha.get("DD", 0)
        nao_classificado = max(0, por_implementadora.get(nome, 0) - tr - dt - dd)
        resumo_implementadoras.append({
            "implementadora": nome,
            "registros": por_implementadora.get(nome, 0),
            "trailer": tr,
            "diesel_truck": dt,
            "direct_drive": dd,
            "nao_classificado": nao_classificado,
            "percentual_mercado_anfir": round(por_implementadora.get(nome, 0) / total * 100, 2) if total else 0.0,
            "variantes_fonte": [
                {"nome": variante, "registros": quantidade}
                for variante, quantidade in variantes[nome].most_common()
            ],
        })

    comparativo_segmentos = _comparativo_segmentos(registros, fora)
    total_segmentos = {
        item["codigo"]: {
            "mercado_total": item["mercado_total"],
            "mercado_excluido": item["mercado_excluido"],
            "mercado_real": item["mercado_real"],
        }
        for item in comparativo_segmentos
    }

    return disputavel, fora, {
        "mercado_anfir_total": total,
        "mercado_fora_escopo_comercial": total_fora,
        "mercado_disputavel_viena": total_disputavel,
        "percentual_fora_escopo": percentual_fora,
        "percentual_disputavel": percentual_disputavel,
        "implementadoras_fora_escopo": resumo_implementadoras,
        "comparativo_mensal": _comparativo_mensal(registros, fora),
        "comparativo_segmentos": comparativo_segmentos,
        "auditoria": {
            "fecha_total": total == total_fora + total_disputavel,
            "formula_total": f"{total} - {total_fora} = {total_disputavel}",
            "segmentos": total_segmentos,
        },
    }
