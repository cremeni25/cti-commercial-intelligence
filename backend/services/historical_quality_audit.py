"""HIST-005 - auditoria automática de qualidade do histórico comercial.

Opera somente em memória sobre resultados do parser, normalização e reconciliação.
Não consulta banco, não grava staging e não promove registros.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Any, Iterable, Mapping


SEVERITY_BY_FLAG = {
    "DIVERGENCIA_ARITMETICA": "ERRO",
    "DATA_INVALIDA": "ERRO",
    "VALOR_TOTAL_AUSENTE_NAO_INFERIDO": "AVISO",
    "PROBABILIDADE_ZERO_NAO_CONFIAVEL": "AVISO",
    "IMPLEMENTADORA_NAO_IDENTIFICADA": "AVISO",
    "IMPLEMENTADORA_COMPOSTA_AMBIGUA": "AVISO",
    "REPRESENTANTE_NAO_INDIVIDUALIZADO": "AVISO",
    "REPRESENTANTE_SUBSTITUIDO_CARLA_POR_MONICA": "INFO",
    "STATUS_INDETERMINADO": "AVISO",
    "EQUIPAMENTO_NAO_CATALOGADO": "INFO",
}

ENTITY_KEYS = ("cliente", "representante", "equipamento", "implementadora")


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _year(record: Any) -> int | None:
    d = _value(record, "data_normalizada")
    return getattr(d, "year", None)


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except Exception:
        return None


@dataclass(frozen=True)
class QualityFinding:
    codigo: str
    severidade: str
    mensagem: str
    aba_origem: str | None = None
    linha_origem: int | None = None
    entidade: str | None = None
    detalhes: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QualityAuditReport:
    total_registros: int
    por_aba: dict[str, int]
    por_ano: dict[str, int]
    por_canal: dict[str, int]
    por_status: dict[str, int]
    reconciliacao: dict[str, dict[str, int]]
    flags: dict[str, int]
    severidades: dict[str, int]
    registros_com_erro: int
    registros_com_aviso: int
    registros_sem_bloqueio: int
    divergencias_aritmeticas: int
    rejeitados: int
    unidades: str
    valor_total_nominal: str
    impacto_analitico_esperado: dict[str, bool]
    findings: tuple[QualityFinding, ...]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["findings"] = [f.as_dict() for f in self.findings]
        return data


def audit_record(record: Any, normalized: Any = None, reconciliations: Mapping[str, Any] | None = None) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    sheet = _value(record, "aba_origem")
    row = _value(record, "linha_origem")
    flags = list(_value(record, "flags_validacao", ()) or ())
    if normalized is not None:
        flags.extend(_value(normalized, "flags_validacao", ()) or ())

    for flag in dict.fromkeys(flags):
        severity = SEVERITY_BY_FLAG.get(flag, "INFO")
        findings.append(QualityFinding(flag, severity, flag.replace("_", " ").title(), sheet, row))

    qty = _to_decimal(_value(normalized, "quantidade_normalizada", _value(record, "quantidade")))
    vu = _to_decimal(_value(normalized, "valor_unitario_normalizado", _value(record, "valor_unitario")))
    vt = _to_decimal(_value(normalized, "valor_total_normalizado", _value(record, "valor_total")))
    if qty is not None and vu is not None and vt is not None and qty * vu != vt and not any(f.codigo == "DIVERGENCIA_ARITMETICA" for f in findings):
        findings.append(QualityFinding("DIVERGENCIA_ARITMETICA", "ERRO", "Quantidade x valor unitário diverge do valor total", sheet, row,
            detalhes={"quantidade": str(qty), "valor_unitario": str(vu), "valor_total": str(vt)}))

    if reconciliations:
        for entity in ENTITY_KEYS:
            result = reconciliations.get(entity)
            if result is None:
                continue
            status = _value(result, "status")
            if status == "AMBIGUO":
                findings.append(QualityFinding("RECONCILIACAO_AMBIGUA", "AVISO", f"{entity} requer revisão humana", sheet, row, entity,
                    {"metodo": _value(result, "metodo"), "confianca": _value(result, "confianca")}))
            elif status == "NAO_ENCONTRADO" and not (_value(result, "flags") and "NAO_APLICAVEL" in _value(result, "flags")):
                findings.append(QualityFinding("ENTIDADE_NAO_ENCONTRADA", "INFO", f"{entity} preservado sem vínculo ao catálogo atual", sheet, row, entity,
                    {"metodo": _value(result, "metodo"), "confianca": _value(result, "confianca")}))
    return findings


def audit_dataset(
    records: Iterable[Any],
    normalized_records: Iterable[Any] | None = None,
    reconciliation_records: Iterable[Mapping[str, Any]] | None = None,
) -> QualityAuditReport:
    records = list(records)
    normalized = list(normalized_records) if normalized_records is not None else [None] * len(records)
    reconciled = list(reconciliation_records) if reconciliation_records is not None else [None] * len(records)
    if len(normalized) != len(records) or len(reconciled) != len(records):
        raise ValueError("records, normalized_records e reconciliation_records devem possuir o mesmo tamanho")

    by_sheet = Counter()
    by_year = Counter()
    by_channel = Counter()
    by_status = Counter()
    flag_counts = Counter()
    severity_counts = Counter()
    reconciliation_counts: dict[str, Counter] = defaultdict(Counter)
    findings: list[QualityFinding] = []
    units = Decimal("0")
    total_value = Decimal("0")
    error_rows: set[int] = set()
    warning_rows: set[int] = set()

    for idx, (record, norm, recs) in enumerate(zip(records, normalized, reconciled)):
        sheet = _value(record, "aba_origem") or "DESCONHECIDA"
        by_sheet[sheet] += 1
        year = _year(record)
        if year is not None:
            by_year[str(year)] += 1
        channel = _value(norm, "canal_venda", _value(record, "canal_venda", "DESCONHECIDO")) or "DESCONHECIDO"
        by_channel[channel] += 1
        status = _value(norm, "status_normalizado", _value(record, "status_normalizado")) or "INDETERMINADO"
        by_status[status] += 1

        qty = _to_decimal(_value(norm, "quantidade_normalizada", _value(record, "quantidade")))
        vt = _to_decimal(_value(norm, "valor_total_normalizado", _value(record, "valor_total")))
        if qty is not None:
            units += qty
        if vt is not None:
            total_value += vt

        if recs:
            for entity in ENTITY_KEYS:
                result = recs.get(entity)
                if result is not None:
                    reconciliation_counts[entity][_value(result, "status", "DESCONHECIDO")] += 1

        row_findings = audit_record(record, norm, recs)
        findings.extend(row_findings)
        for finding in row_findings:
            flag_counts[finding.codigo] += 1
            severity_counts[finding.severidade] += 1
            if finding.severidade in ("ERRO", "BLOQUEIO"):
                error_rows.add(idx)
            elif finding.severidade == "AVISO":
                warning_rows.add(idx)

    rejected = len(error_rows)
    without_block = len(records) - rejected
    impact = {
        "conversao_historica": bool(by_status),
        "mix_equipamentos": bool(records),
        "analise_perdas": any(k == "PERDIDO" for k in by_status),
        "canal_direto_vs_oem": len(by_channel) > 1 or "INDIRETA_OEM" in by_channel,
        "responsabilidade_territorial_atual": bool(records),
        "cruzamento_anfir_crm": False,
    }
    return QualityAuditReport(
        total_registros=len(records),
        por_aba=dict(sorted(by_sheet.items())),
        por_ano=dict(sorted(by_year.items())),
        por_canal=dict(sorted(by_channel.items())),
        por_status=dict(sorted(by_status.items())),
        reconciliacao={k: dict(sorted(v.items())) for k, v in sorted(reconciliation_counts.items())},
        flags=dict(sorted(flag_counts.items())),
        severidades=dict(sorted(severity_counts.items())),
        registros_com_erro=len(error_rows),
        registros_com_aviso=len(warning_rows - error_rows),
        registros_sem_bloqueio=without_block,
        divergencias_aritmeticas=flag_counts.get("DIVERGENCIA_ARITMETICA", 0),
        rejeitados=rejected,
        unidades=str(units.normalize()),
        valor_total_nominal=str(total_value.quantize(Decimal("0.01"))),
        impacto_analitico_esperado=impact,
        findings=tuple(findings),
    )
