from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def _quantidade(item: dict[str, Any]) -> int:
    try:
        valor = item.get("quantidade")
        if valor in (None, ""):
            return 1
        return max(0, int(float(valor)))
    except (TypeError, ValueError):
        return 1


def _fabricante_estruturado(item: dict[str, Any]) -> str | None:
    bruto = _fold(item.get("fabricante_equipamento"))
    if bruto in {"", "NAN", "NONE", "80", "#N/A", "N/A", "DOCUMENTACAO"}:
        return None
    aliases = {
        "CARRRIER": "CARRIER",
        "CARRIER TRANSICOLD": "CARRIER",
        "THERMO KING": "THERMO KING",
        "THERMO-KING": "THERMO KING",
        "THERMOKING": "THERMO KING",
        "TK": "THERMO KING",
    }
    return aliases.get(bruto, bruto)


def composicao_marca_linha(registros: list[dict[str, Any]]) -> dict[str, Any]:
    """Fecha 100% do mercado da linha antes de qualquer interpretação competitiva.

    Hierarquia obrigatória:
    1) o total do mercado vem da linha/segmento;
    2) depois se identifica Carrier confirmado;
    3) depois outras marcas confirmadas;
    4) o que não tem evidência suficiente permanece como marca não discriminada.

    Nenhuma unidade some do denominador e nenhuma marca é inventada.
    """
    carrier = 0
    concorrentes: Counter[str] = Counter()
    nao_discriminada = 0
    total = 0

    for item in registros:
        quantidade = _quantidade(item)
        total += quantidade
        status = _fold(item.get("status")).replace(" ", "")
        fabricante = _fabricante_estruturado(item)

        if status in {"CARRIER", "USADOCARRIER"}:
            carrier += quantidade
            continue

        if status == "TK":
            concorrentes["THERMO KING"] += quantidade
            continue

        if status in {"NACIONAL", "USADOCONCORRENTE"}:
            if fabricante and fabricante != "CARRIER":
                concorrentes[fabricante] += quantidade
            else:
                concorrentes["OUTRA MARCA — NÃO DISCRIMINADA"] += quantidade
            continue

        if fabricante == "CARRIER":
            carrier += quantidade
            continue

        if fabricante:
            concorrentes[fabricante] += quantidade
            continue

        nao_discriminada += quantidade

    outras_marcas = sum(concorrentes.values())
    fechamento = carrier + outras_marcas + nao_discriminada

    def pct(valor: int) -> float:
        return round((valor / total) * 100, 2) if total else 0.0

    return {
        "mercado": total,
        "carrier": carrier,
        "outras_marcas": outras_marcas,
        "marca_nao_discriminada": nao_discriminada,
        "carrier_pct": pct(carrier),
        "outras_marcas_pct": pct(outras_marcas),
        "marca_nao_discriminada_pct": pct(nao_discriminada),
        "fechamento_total": fechamento,
        "fechamento_ok": fechamento == total,
        "marcas_concorrentes": [
            {"nome": nome, "quantidade": quantidade, "percentual_mercado": pct(quantidade)}
            for nome, quantidade in concorrentes.most_common()
        ],
        "regra": "LINHA_PRIMEIRO_DEPOIS_MARCA; TOTAL=100%; SEM_INFERENCIA_DE_MARCA",
    }
