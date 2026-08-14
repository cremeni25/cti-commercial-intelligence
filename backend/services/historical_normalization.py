"""HIST-003 - normalizadores determinísticos do histórico comercial.

Este módulo não acessa banco, não promove registros e não altera entidades operacionais.
Ele transforma somente representações em memória preservando o valor original.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from typing import Any

from core.cti_taxonomy import consolidar_cliente, normalizar_implementadora

REPRESENTANTES = {
    "ANDERSON": "ANDERSON - VIENA SP",
    "ANDRE": "ANDRE - VIENA SP",
    "NATHAN": "NATHAN - VIENA SP",
    "MICHELE": "MICHELE - VIENA SP",
    "MONICA": "MÔNICA - VIENA SP",
    "MÔNICA": "MÔNICA - VIENA SP",
}

MESES = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4,
    "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8,
    "SETEMBRO": 9, "SETEMBO": 9, "OUTUBRO": 10,
    "NOVEMBRO": 11, "DEZEMBRO": 12,
}

EQUIP_ALIASES = {
    "X4 7500": "X4 7500",
    "X4-7500": "X4 7500",
    "VECTOR 8500": "VECTOR 8500",
    "VECTOR HE19": "VECTOR HE19",
    "SUPRA 750": "SUPRA 750",
    "SUPRA 850": "SUPRA 850",
    "SUPRA 1150": "SUPRA 1150",
    "CITIMAX 280": "CITIMAX 280",
    "CITIMAX 400": "CITIMAX 400",
    "CITIMAX 500": "CITIMAX 500",
}


def clean(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def fold(value: Any) -> str:
    text = clean(value) or ""
    text = "".join(c for c in unicodedata.normalize("NFKD", text.upper()) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


def decimal_ptbr(value: Any) -> Decimal | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = clean(value)
    if not text or text.startswith("="):
        return None
    text = text.replace("R$", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def normalize_cliente(value: Any) -> str | None:
    original = clean(value)
    return consolidar_cliente(original) if original else None


def normalize_representante(value: Any) -> tuple[str | None, list[str]]:
    original = clean(value)
    if not original:
        return None, ["REPRESENTANTE_AUSENTE"]
    f = fold(original)
    if "CARLA" in f:
        return "MÔNICA - VIENA SP", ["REPRESENTANTE_SUBSTITUIDO_CARLA_POR_MONICA"]
    if f == "VIENA SP":
        return "VIENA SP", ["REPRESENTANTE_NAO_INDIVIDUALIZADO"]
    for token, official in REPRESENTANTES.items():
        if fold(token) in f:
            return official, []
    return f, ["REPRESENTANTE_NAO_CATALOGADO"]


def normalize_equipamento(value: Any) -> tuple[str | None, list[str]]:
    original = clean(value)
    if not original:
        return None, ["EQUIPAMENTO_AUSENTE"]
    f = fold(original).replace("  ", " ")
    canonical = EQUIP_ALIASES.get(f, f)
    flags = [] if canonical in EQUIP_ALIASES.values() else ["EQUIPAMENTO_NAO_CATALOGADO"]
    return canonical, flags


def normalize_data(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = clean(value)
    if not text:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def normalize_previsao(value: Any, ano_referencia: int | None = None) -> dict[str, Any]:
    if isinstance(value, (date, datetime)):
        d = value.date() if isinstance(value, datetime) else value
        return {"previsao_mes": d.month, "previsao_ano": d.year, "previsao_data": d, "precisao_previsao": "DATA"}
    f = fold(value)
    if not f:
        return {"previsao_mes": None, "previsao_ano": None, "previsao_data": None, "precisao_previsao": "DESCONHECIDA"}
    if f in MESES:
        return {"previsao_mes": MESES[f], "previsao_ano": ano_referencia, "previsao_data": None, "precisao_previsao": "MES"}
    d = normalize_data(value)
    if d:
        return {"previsao_mes": d.month, "previsao_ano": d.year, "previsao_data": d, "precisao_previsao": "DATA"}
    return {"previsao_mes": None, "previsao_ano": ano_referencia, "previsao_data": None, "precisao_previsao": "DESCONHECIDA"}


def normalize_probabilidade(value: Any, aba_origem: str | None = None) -> tuple[Decimal | None, Decimal | None, list[str]]:
    d = decimal_ptbr(value)
    if d is None:
        return None, None, ["PROBABILIDADE_AUSENTE_OU_INVALIDA"]
    if Decimal("1") < d <= Decimal("100"):
        d = d / Decimal("100")
    if d < 0 or d > 1:
        return None, Decimal("0"), ["PROBABILIDADE_FORA_FAIXA"]
    if aba_origem == "OPORTUNIDADE" and d == 0:
        return d, Decimal("0"), ["PROBABILIDADE_ZERO_NAO_CONFIAVEL"]
    return d, Decimal("1"), []


def normalize_status(observacao: Any, aba_origem: str | None = None) -> tuple[str | None, str | None, list[str]]:
    f = fold(observacao)
    if not f:
        return None, None, ["STATUS_NAO_IDENTIFICADO"]
    if "SEM RETORNO" in f:
        return "PERDIDO", "SEM_RETORNO", []
    if any(x in f for x in ("CANCEL", "DECLIN", "PERDEMOS", "PERDEU")):
        motivo = "PRECO" if "PRECO" in f else ("CONCORRENCIA" if "CONCORREN" in f else "OUTRO")
        return "PERDIDO", motivo, []
    if "CONCORREN" in f and any(x in f for x in ("PERDEU", "PERDEMOS", "FECHOU COM")):
        return "PERDIDO", "CONCORRENCIA", []
    if any(x in f for x in ("CONCLUID", "FINALIZ", "FECHOU", "GANHAMOS", "FECHADO")):
        return "GANHO", None, []
    if "SO FATURAR" in f or "AGUARDANDO FATUR" in f:
        return "FATURAMENTO_PENDENTE", None, []
    if "AGUARDANDO PAGAMENTO" in f or "AGUARDANDO BANCO" in f:
        return "FINANCEIRO_PENDENTE", None, []
    if "DEMONSTRAC" in f:
        return "DEMONSTRACAO", None, []
    if any(x in f for x in ("NEGOCI", "COTAC", "ANALISE")):
        return "EM_NEGOCIACAO", "PRECO" if "PRECO" in f else None, []
    if aba_origem == "BACKLOG" and "FATUR" in f:
        return "FATURAMENTO_PENDENTE", None, []
    return "INDETERMINADO", None, ["STATUS_INDETERMINADO"]


def normalize_implementadora(value: Any) -> tuple[str | None, list[str]]:
    original = clean(value)
    if not original:
        return None, ["IMPLEMENTADORA_NAO_IDENTIFICADA"]
    f = fold(original)
    if "BORTOLOTO" in f and "IBIPORA" in f:
        return "IBIPORÃ", ["IMPLEMENTADORA_ALIAS_BORTOLOTO_IBIPORA"]
    if f == "FRATELLI":
        return "FRATELI", ["IMPLEMENTADORA_ALIAS_FRATELLI_FRATELI"]
    if "/" in original:
        return None, ["IMPLEMENTADORA_COMPOSTA_AMBIGUA"]
    normalized = normalizar_implementadora(original)
    return normalized, [] if normalized else ["IMPLEMENTADORA_NAO_CATALOGADA"]


@dataclass(frozen=True)
class NormalizedHistoricalRecord:
    cliente_normalizado: str | None
    representante_normalizado: str | None
    equipamento_normalizado: str | None
    quantidade_normalizada: Decimal | None
    valor_unitario_normalizado: Decimal | None
    valor_total_normalizado: Decimal | None
    data_normalizada: date | None
    previsao_mes: int | None
    previsao_ano: int | None
    previsao_data: date | None
    precisao_previsao: str
    probabilidade_normalizada: Decimal | None
    confianca_probabilidade: Decimal | None
    status_normalizado: str | None
    motivo_perda_normalizado: str | None
    canal_venda: str
    implementadora_normalizada: str | None
    flags_validacao: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_record(record: Any) -> NormalizedHistoricalRecord:
    flags: list[str] = []
    rep, f = normalize_representante(getattr(record, "representante_original", None)); flags += f
    equip, f = normalize_equipamento(getattr(record, "equipamento_original", None)); flags += f
    prob, prob_conf, f = normalize_probabilidade(getattr(record, "probabilidade_original", None), getattr(record, "aba_origem", None)); flags += f
    status, motivo, f = normalize_status(getattr(record, "observacao_original", None), getattr(record, "aba_origem", None)); flags += f
    previsao = normalize_previsao(getattr(record, "previsao_original", None), getattr(getattr(record, "data_normalizada", None), "year", None))
    canal = getattr(record, "canal_venda", None) or ("INDIRETA_OEM" if getattr(record, "aba_origem", None) == "INTERMEDIAÇÃO - OEM" else "DIRETA")
    impl = None
    if canal == "INDIRETA_OEM":
        impl, f = normalize_implementadora(getattr(record, "implementadora_original", None)); flags += f
    qty = decimal_ptbr(getattr(record, "quantidade", None))
    vu = decimal_ptbr(getattr(record, "valor_unitario", None))
    vt = decimal_ptbr(getattr(record, "valor_total", None))
    return NormalizedHistoricalRecord(
        cliente_normalizado=normalize_cliente(getattr(record, "cliente_original", None)),
        representante_normalizado=rep,
        equipamento_normalizado=equip,
        quantidade_normalizada=qty,
        valor_unitario_normalizado=vu,
        valor_total_normalizado=vt,
        data_normalizada=normalize_data(getattr(record, "data_normalizada", None) or getattr(record, "data_original", None)),
        previsao_mes=previsao["previsao_mes"], previsao_ano=previsao["previsao_ano"],
        previsao_data=previsao["previsao_data"], precisao_previsao=previsao["precisao_previsao"],
        probabilidade_normalizada=prob, confianca_probabilidade=prob_conf,
        status_normalizado=status, motivo_perda_normalizado=motivo,
        canal_venda=canal, implementadora_normalizada=impl,
        flags_validacao=tuple(dict.fromkeys(flags)),
    )
