from __future__ import annotations

import re
import unicodedata
from collections import Counter
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


def _status_fonte(registro: dict[str, Any]) -> str:
    return _sem_acento(registro.get("status")).replace(" ", "")


def _fabricante_estruturado(registro: dict[str, Any], taxonomia: dict[str, str]) -> str | None:
    bruto = _sem_acento(registro.get("fabricante_equipamento"))
    return taxonomia.get(bruto) if bruto else None


def _classificar_registro(registro: dict[str, Any], taxonomia: dict[str, str]) -> tuple[str, str | None, str | None]:
    """Classifica a fotografia competitiva sem transformar menções textuais em fatos."""
    status = _status_fonte(registro)
    fabricante_bruto = _sem_acento(registro.get("fabricante_equipamento"))
    fabricante = _fabricante_estruturado(registro, taxonomia)

    if fabricante_bruto in {_sem_acento(v) for v in STATUS_DOCUMENTACAO}:
        return "REAPROVEITAMENTO_DOCUMENTACAO", None, "DOCUMENTACAO_REAPROVEITAMENTO"
    if status == "CARRIER":
        return "CARRIER", "CARRIER", None
    if status == "TK":
        return "CONCORRENCIA", "THERMOKING", None
    if status == "NACIONAL":
        if fabricante and fabricante not in {"CARRIER", "THERMOKING"}:
            return "CONCORRENCIA", fabricante, None
        return "CONCORRENCIA_NACIONAL_NAO_IDENTIFICADA", None, None
    if status == "USADOCONCORRENTE":
        return "USADO_CONCORRENTE", fabricante if fabricante and fabricante != "CARRIER" else None, None
    if status == "USADOCARRIER":
        return "USADO_CARRIER", "CARRIER", None
    if status == "SEMCONTATO":
        return "SEM_CONTATO", None, None
    return "A_IDENTIFICAR", None, None


def _aplicar_classificacao_cti(
    registro: dict[str, Any],
    grupo: str,
    fabricante: str | None,
    taxonomia: dict[str, str],
    overrides: dict[str, str],
) -> tuple[str, str | None, bool]:
    """Aplica somente a camada comercial CTI permitida, preservando a categoria Carrier/JOV.

    TK e CARRIER permanecem fechadas pela fonte oficial. NACIONAL pode ganhar a marca
    concorrente identificada pelo Master sem alterar a categoria original. Usado concorrente
    e A_IDENTIFICAR também podem receber uma marca para ação comercial, mas continuam fora do
    market share de equipamentos novos quando a fonte não os classificou como compra nova.
    """
    registro_id = str(registro.get("id") or "")
    override_bruto = overrides.get(registro_id)
    override = taxonomia.get(_sem_acento(override_bruto)) if override_bruto else None
    if not override or override == "CARRIER":
        return grupo, fabricante, False

    status = _status_fonte(registro)
    if status in {"CARRIER", "TK"}:
        return grupo, fabricante, False
    if status == "NACIONAL":
        if override == "THERMOKING":
            return grupo, fabricante, False
        return "CONCORRENCIA", override, True
    if status == "USADOCONCORRENTE":
        return "USADO_CONCORRENTE", override, True
    if grupo == "A_IDENTIFICAR":
        return "A_IDENTIFICAR", override, True
    return grupo, fabricante, False


def _percentual(parte: int, total: int) -> float:
    return round((parte / total) * 100, 2) if total else 0.0


def consolidar_competitividade_anfir_2026(
    registros: list[dict[str, Any]],
    fabricantes_canonicos: list[str],
    classificacoes_cti: dict[str, str] | None = None,
) -> dict[str, Any]:
    registros_2026 = [dict(r) for r in registros if (d := data_registro(r)) and d.year == 2026]
    taxonomia = _normalizar_taxonomia(fabricantes_canonicos)
    fabricantes_validos = sorted(set(taxonomia.values()))
    overrides = classificacoes_cti or {}

    enriquecidos: list[dict[str, Any]] = []
    for registro in registros_2026:
        grupo_fonte, fabricante_fonte, status_especial = _classificar_registro(registro, taxonomia)
        grupo, fabricante, classificado_cti = _aplicar_classificacao_cti(
            registro, grupo_fonte, fabricante_fonte, taxonomia, overrides
        )
        linha = _linha(registro)
        data = data_registro(registro)
        enriquecidos.append({
            **registro,
            "linha_competitiva": linha,
            "fabricante_competitivo": fabricante,
            "fabricante_fonte": fabricante_fonte,
            "fabricante_bruto": str(registro.get("fabricante_equipamento") or "").strip(),
            "fabricante_cti": overrides.get(str(registro.get("id") or "")) if classificado_cti else None,
            "classificado_cti": classificado_cti,
            "grupo_competitivo": grupo,
            "grupo_fonte": grupo_fonte,
            "status_competitivo": status_especial,
            "competencia": f"{data.year:04d}-{data.month:02d}" if data else None,
        })

    segmentos = []
    ranking_total: Counter[str] = Counter()
    documentacao_total = 0
    nacional_nao_identificada_total = 0
    usado_concorrente_total = 0
    usado_carrier_total = 0
    sem_contato_total = 0

    for codigo in SEGMENTOS:
        itens = [r for r in enriquecidos if r["linha_competitiva"] == codigo]
        mercado = len(itens)
        carrier = sum(1 for r in itens if r["grupo_competitivo"] == "CARRIER")
        concorrencia_identificada = sum(1 for r in itens if r["grupo_competitivo"] == "CONCORRENCIA")
        nacional_nao_identificada = sum(1 for r in itens if r["grupo_competitivo"] == "CONCORRENCIA_NACIONAL_NAO_IDENTIFICADA")
        concorrencia = concorrencia_identificada + nacional_nao_identificada
        documentacao = sum(1 for r in itens if r["grupo_competitivo"] == "REAPROVEITAMENTO_DOCUMENTACAO")
        usado_concorrente = sum(1 for r in itens if r["grupo_competitivo"] == "USADO_CONCORRENTE")
        usado_carrier = sum(1 for r in itens if r["grupo_competitivo"] == "USADO_CARRIER")
        sem_contato = sum(1 for r in itens if r["grupo_competitivo"] == "SEM_CONTATO")
        a_identificar = sum(1 for r in itens if r["grupo_competitivo"] == "A_IDENTIFICAR")
        fabricantes = Counter(
            str(r["fabricante_competitivo"])
            for r in itens
            if r["grupo_competitivo"] == "CONCORRENCIA" and r.get("fabricante_competitivo")
        )
        ranking_total.update(fabricantes)
        documentacao_total += documentacao
        nacional_nao_identificada_total += nacional_nao_identificada
        usado_concorrente_total += usado_concorrente
        usado_carrier_total += usado_carrier
        sem_contato_total += sem_contato

        mensal = []
        for mes_num in range(1, 13):
            mes_itens = [r for r in itens if r.get("competencia") == f"2026-{mes_num:02d}"]
            if not mes_itens:
                continue
            mes_concorrencia = sum(1 for r in mes_itens if r["grupo_competitivo"] in {"CONCORRENCIA", "CONCORRENCIA_NACIONAL_NAO_IDENTIFICADA"})
            mensal.append({
                "mes": MESES[mes_num],
                "competencia": f"2026-{mes_num:02d}",
                "carrier": sum(1 for r in mes_itens if r["grupo_competitivo"] == "CARRIER"),
                "concorrencia": mes_concorrencia,
                "thermoking": sum(1 for r in mes_itens if r.get("fabricante_competitivo") == "THERMOKING" and r["grupo_competitivo"] == "CONCORRENCIA"),
                "nacional": sum(1 for r in mes_itens if _status_fonte(r) == "NACIONAL"),
                "reaproveitamento": sum(1 for r in mes_itens if r["grupo_competitivo"] in {"REAPROVEITAMENTO_DOCUMENTACAO", "USADO_CONCORRENTE", "USADO_CARRIER"}),
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
            "thermoking": fabricantes.get("THERMOKING", 0),
            "nacional": sum(1 for r in itens if _status_fonte(r) == "NACIONAL"),
            "nacional_fabricante_nao_identificado": nacional_nao_identificada,
            "usado_concorrente": usado_concorrente,
            "usado_carrier": usado_carrier,
            "sem_contato": sem_contato,
            "reaproveitamento_documentacao": documentacao,
            "a_identificar": a_identificar,
            "fabricantes_concorrentes": [
                {"fabricante": nome, "registros": qtd, "percentual_mercado": _percentual(qtd, mercado)}
                for nome, qtd in fabricantes.most_common()
            ],
            "mensal": mensal,
        })

    total = len(enriquecidos)
    carrier_total = sum(1 for r in enriquecidos if r["grupo_competitivo"] == "CARRIER")
    concorrencia_total = sum(1 for r in enriquecidos if r["grupo_competitivo"] in {"CONCORRENCIA", "CONCORRENCIA_NACIONAL_NAO_IDENTIFICADA"})
    a_identificar_total = sum(1 for r in enriquecidos if r["grupo_competitivo"] == "A_IDENTIFICAR")

    detalhes = []
    for r in enriquecidos:
        detalhes.append({
            "id": r.get("id"),
            "data": str(r.get("data_venda") or ""),
            "cliente": r.get("cliente"),
            "cnpj": r.get("cnpj"),
            "cidade": r.get("cidade"),
            "estado": r.get("estado"),
            "ddd": r.get("ddd"),
            "segmento": r.get("linha_competitiva"),
            "linha_original": r.get("linha"),
            "fabricante": r.get("fabricante_competitivo"),
            "fabricante_fonte": r.get("fabricante_fonte"),
            "fabricante_bruto": r.get("fabricante_bruto"),
            "fabricante_cti": r.get("fabricante_cti"),
            "classificado_cti": r.get("classificado_cti"),
            "grupo": r.get("grupo_competitivo"),
            "grupo_fonte": r.get("grupo_fonte"),
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
            "regra_competitividade": "A categoria/status Carrier/JOV é a fonte primária do resultado observado. A classificação CTI pode identificar a marca concorrente sem alterar o dado bruto nem converter menções textuais em market share.",
            "regra_edicao": "Edições de fabricante são gravadas em camada CTI auditável e nunca alteram cti_anfir. CARRIER e TK oficiais não podem ser reclassificados por esta função.",
            "regra_documentacao": "DOCUMENTAÇÃO não é fabricante. Representa regularização documental do reaproveitamento do conjunto baú/equipamento quando há troca do caminhão; deve ser lida como retenção/reaproveitamento de ativo, não como concorrência nova.",
        },
        "resumo": {
            "mercado": total,
            "carrier": carrier_total,
            "carrier_percentual": _percentual(carrier_total, total),
            "concorrencia_identificada": concorrencia_total,
            "concorrencia_percentual": _percentual(concorrencia_total, total),
            "thermoking": ranking_total.get("THERMOKING", 0),
            "nacional_fabricante_nao_identificado": nacional_nao_identificada_total,
            "usado_concorrente": usado_concorrente_total,
            "usado_carrier": usado_carrier_total,
            "sem_contato": sem_contato_total,
            "reaproveitamento_documentacao": documentacao_total,
            "a_identificar": a_identificar_total,
        },
        "ranking_concorrentes": [
            {"fabricante": nome, "registros": qtd, "percentual_mercado": _percentual(qtd, total)}
            for nome, qtd in ranking_total.most_common()
        ],
        "segmentos": segmentos,
        "leituras_estrategicas": [
            "A leitura competitiva usa a categoria oficial Carrier/JOV como verdade primária do resultado observado; menções em texto não são convertidas em vendas ou market share.",
            "Thermo King é contabilizada quando a categoria/status é TK, independentemente de o campo auxiliar fabricante_equipamento estar vazio.",
            "NACIONAL compõe concorrência; a marca específica pode ser confirmada na camada CTI por registro/cliente sem modificar a planilha Carrier/JOV original.",
            "Usado concorrente, usado Carrier, sem contato e documentação permanecem indicadores estratégicos separados e não inflam a concorrência de equipamentos novos.",
        ],
        "detalhes": detalhes,
    }
