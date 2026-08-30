from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

from services.operational_filters import data_registro
from services.product_line_classifier import classificar_linha

SEGMENTOS = ("TR", "DT", "DD")
NOMES_SEGMENTOS = {"TR": "Trailer", "DT": "Diesel Truck", "DD": "Direct Drive"}
MESES = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

ALIASES_FIXOS = {
    "CARRRIER": "CARRIER",
    "CARRIER TRANSICOLD": "CARRIER",
    "THERMO KING": "THERMOKING",
    "THERMO-KING": "THERMOKING",
    "TK": "THERMOKING",
    "PALACIO": "PALACIO",
    "PALÁCIO": "PALACIO",
}

STATUS_DOCUMENTACAO = {"DOCUMENTACAO", "DOCUMENTAÇÃO"}


def _sem_acento(valor: Any) -> str:
    texto = str(valor or "").strip().upper()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def _normalizar_taxonomia(fabricantes: list[str]) -> dict[str, str]:
    retorno: dict[str, str] = {}
    for nome in fabricantes:
        canonico = str(nome or "").strip().upper()
        if canonico:
            retorno[_sem_acento(canonico)] = canonico
    for alias, canonico in ALIASES_FIXOS.items():
        retorno[_sem_acento(alias)] = canonico
    return retorno


def _linha(registro: dict[str, Any]) -> str:
    return classificar_linha(registro) or "UNKNOWN"


def _fabricante_e_status(registro: dict[str, Any], taxonomia: dict[str, str]) -> tuple[str | None, str | None, str]:
    bruto = str(registro.get("fabricante_equipamento") or "").strip()
    bruto_norm = _sem_acento(bruto)
    if bruto_norm in {_sem_acento(v) for v in STATUS_DOCUMENTACAO}:
        return None, "DOCUMENTACAO_REAPROVEITAMENTO", bruto

    if bruto_norm:
        canonico = taxonomia.get(bruto_norm)
        if canonico:
            return canonico, None, bruto

    texto_contexto = _sem_acento(" ".join(str(registro.get(c) or "") for c in ("ocorrencia", "motivo", "status")))
    for chave, canonico in sorted(taxonomia.items(), key=lambda item: len(item[0]), reverse=True):
        if len(chave) < 3:
            continue
        if re.search(rf"(?<![A-Z0-9]){re.escape(chave)}(?![A-Z0-9])", texto_contexto):
            return canonico, None, bruto
    return None, None, bruto


def _percentual(parte: int, total: int) -> float:
    return round((parte / total) * 100, 2) if total else 0.0


def consolidar_competitividade_anfir_2026(registros: list[dict[str, Any]], fabricantes_canonicos: list[str]) -> dict[str, Any]:
    registros_2026 = [dict(r) for r in registros if (d := data_registro(r)) and d.year == 2026]
    taxonomia = _normalizar_taxonomia(fabricantes_canonicos)
    fabricantes_validos = sorted(set(taxonomia.values()))

    enriquecidos: list[dict[str, Any]] = []
    for registro in registros_2026:
        fabricante, status_especial, fabricante_bruto = _fabricante_e_status(registro, taxonomia)
        linha = _linha(registro)
        data = data_registro(registro)
        grupo = "A_IDENTIFICAR"
        if fabricante == "CARRIER":
            grupo = "CARRIER"
        elif fabricante:
            grupo = "CONCORRENCIA"
        elif status_especial == "DOCUMENTACAO_REAPROVEITAMENTO":
            grupo = "REAPROVEITAMENTO"
        enriquecidos.append({
            **registro,
            "linha_competitiva": linha,
            "fabricante_competitivo": fabricante,
            "fabricante_bruto": fabricante_bruto,
            "grupo_competitivo": grupo,
            "status_competitivo": status_especial,
            "competencia": f"{data.year:04d}-{data.month:02d}" if data else None,
        })

    segmentos = []
    ranking_total: Counter[str] = Counter()
    documentacao_total = 0
    for codigo in SEGMENTOS:
        itens = [r for r in enriquecidos if r["linha_competitiva"] == codigo]
        mercado = len(itens)
        carrier = sum(1 for r in itens if r["grupo_competitivo"] == "CARRIER")
        concorrencia = sum(1 for r in itens if r["grupo_competitivo"] == "CONCORRENCIA")
        documentacao = sum(1 for r in itens if r["grupo_competitivo"] == "REAPROVEITAMENTO")
        a_identificar = mercado - carrier - concorrencia - documentacao
        fabricantes = Counter(str(r["fabricante_competitivo"]) for r in itens if r["grupo_competitivo"] == "CONCORRENCIA" and r.get("fabricante_competitivo"))
        ranking_total.update(fabricantes)
        documentacao_total += documentacao
        mensal = []
        for mes_num in range(1, 13):
            mes_itens = [r for r in itens if r.get("competencia") == f"2026-{mes_num:02d}"]
            if not mes_itens:
                continue
            mensal.append({
                "mes": MESES[mes_num],
                "competencia": f"2026-{mes_num:02d}",
                "carrier": sum(1 for r in mes_itens if r["grupo_competitivo"] == "CARRIER"),
                "concorrencia": sum(1 for r in mes_itens if r["grupo_competitivo"] == "CONCORRENCIA"),
                "reaproveitamento": sum(1 for r in mes_itens if r["grupo_competitivo"] == "REAPROVEITAMENTO"),
                "a_identificar": sum(1 for r in mes_itens if r["grupo_competitivo"] == "A_IDENTIFICAR"),
                "mercado": len(mes_itens),
            })
        segmentos.append({
            "codigo": codigo,
            "segmento": NOMES_SEGMENTOS[codigo],
            "mercado": mercado,
            "carrier": carrier,
            "carrier_percentual": _percentual(carrier, mercado),
            "concorrencia": concorrencia,
            "concorrencia_percentual": _percentual(concorrencia, mercado),
            "reaproveitamento_documentacao": documentacao,
            "a_identificar": a_identificar,
            "fabricantes_concorrentes": [{"fabricante": nome, "registros": qtd, "percentual_mercado": _percentual(qtd, mercado)} for nome, qtd in fabricantes.most_common()],
            "mensal": mensal,
        })

    total = len(enriquecidos)
    carrier_total = sum(1 for r in enriquecidos if r["grupo_competitivo"] == "CARRIER")
    concorrencia_total = sum(1 for r in enriquecidos if r["grupo_competitivo"] == "CONCORRENCIA")
    a_identificar_total = sum(1 for r in enriquecidos if r["grupo_competitivo"] == "A_IDENTIFICAR")

    detalhes = []
    for r in enriquecidos:
        detalhes.append({
            "id": r.get("id"),
            "data": str(r.get("data_venda") or ""),
            "cliente": r.get("cliente"),
            "cidade": r.get("cidade"),
            "estado": r.get("estado"),
            "ddd": r.get("ddd"),
            "segmento": r.get("linha_competitiva"),
            "linha_original": r.get("linha"),
            "fabricante": r.get("fabricante_competitivo"),
            "fabricante_bruto": r.get("fabricante_bruto"),
            "grupo": r.get("grupo_competitivo"),
            "status_competitivo": r.get("status_competitivo"),
            "status": r.get("status"),
            "motivo": r.get("motivo"),
            "ocorrencia": r.get("ocorrencia"),
            "competencia": r.get("competencia"),
        })

    return {
        "metadata": {
            "competencia": "2026",
            "fonte_taxonomia": "cti_fabricantes",
            "fabricantes_ativos": fabricantes_validos,
            "regra_documentacao": "DOCUMENTAÇÃO não é fabricante. Representa regularização documental do reaproveitamento do conjunto baú/equipamento quando há troca do caminhão; deve ser lida como retenção/reaproveitamento de ativo, não como concorrência.",
        },
        "resumo": {
            "mercado": total,
            "carrier": carrier_total,
            "carrier_percentual": _percentual(carrier_total, total),
            "concorrencia_identificada": concorrencia_total,
            "concorrencia_percentual": _percentual(concorrencia_total, total),
            "reaproveitamento_documentacao": documentacao_total,
            "a_identificar": a_identificar_total,
        },
        "ranking_concorrentes": [{"fabricante": nome, "registros": qtd, "percentual_mercado": _percentual(qtd, total)} for nome, qtd in ranking_total.most_common()],
        "segmentos": segmentos,
        "leituras_estrategicas": [
            "Carrier deve ser comparada com a concorrência identificada por fabricante, usando a taxonomia oficial do CTI; Thermo King deixa de ser coluna fixa e passa a compor o ranking competitivo como qualquer outro fabricante.",
            "TR, DT e DD possuem dinâmicas competitivas diferentes e são acompanhados separadamente, inclusive na evolução mensal Carrier × concorrência.",
            "DOCUMENTAÇÃO é tratada como reaproveitamento do conjunto baú/equipamento com regularização do implemento (ex.: operação FWest), portanto representa retenção de ativo e adiamento/substituição da compra de equipamento, não fabricante concorrente.",
            "Registros sem fabricante identificado permanecem em 'A identificar' e não são artificialmente atribuídos a concorrentes.",
        ],
        "detalhes": detalhes,
    }
