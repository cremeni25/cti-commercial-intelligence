from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

IMPLEMENTADORAS_FORA_ESCOPO = ("FIBRA WEST", "HIFLEX", "PLANALTO")


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
    if "HIFLEX" in nome or "HI FLEX" in nome:
        return "HIFLEX"
    if "PLANALTO" in nome:
        return "PLANALTO"
    return None


def particionar_mercado_disputavel(
    registros: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    disputavel: list[dict[str, Any]] = []
    fora: list[dict[str, Any]] = []
    por_implementadora: Counter[str] = Counter()
    variantes: dict[str, Counter[str]] = defaultdict(Counter)

    for item in registros:
        registro = dict(item)
        canonico = implementadora_fora_escopo(registro)
        if not canonico:
            disputavel.append(registro)
            continue
        fora.append(registro)
        por_implementadora[canonico] += 1
        bruto = str(registro.get("implementadora") or registro.get("implementador") or canonico).strip()
        variantes[canonico][bruto or canonico] += 1

    total = len(registros)
    total_fora = len(fora)
    total_disputavel = len(disputavel)
    percentual_fora = round(total_fora / total * 100, 2) if total else 0.0
    percentual_disputavel = round(total_disputavel / total * 100, 2) if total else 0.0

    resumo_implementadoras = []
    for nome in IMPLEMENTADORAS_FORA_ESCOPO:
        resumo_implementadoras.append({
            "implementadora": nome,
            "registros": por_implementadora.get(nome, 0),
            "percentual_mercado_anfir": round(por_implementadora.get(nome, 0) / total * 100, 2) if total else 0.0,
            "variantes_fonte": [
                {"nome": variante, "registros": quantidade}
                for variante, quantidade in variantes[nome].most_common()
            ],
        })

    return disputavel, fora, {
        "mercado_anfir_total": total,
        "mercado_fora_escopo_comercial": total_fora,
        "mercado_disputavel_viena": total_disputavel,
        "percentual_fora_escopo": percentual_fora,
        "percentual_disputavel": percentual_disputavel,
        "implementadoras_fora_escopo": resumo_implementadoras,
        "regra": (
            "Fibra West, HiFlex e Planalto permanecem visíveis como mercado ANFIR observado, "
            "mas são retiradas do denominador comercial da Viena por impossibilidade estrutural de atendimento."
        ),
    }
