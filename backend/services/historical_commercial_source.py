from __future__ import annotations

import base64
import csv
import gzip
import io
import json
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

SOURCE_FILE = "funil de vendas 2026(20260814-104652).xlsx"
SOURCE_SHA256 = "54bb20087d96013e5a814a1d378f37315987c56b4a617631bd9603725ebb4583"
SOURCE_TOTAL = 906
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "historico_comercial"
PARTS = tuple(DATA_DIR / f"historico_2023_2026.b64.part{i}" for i in range(1, 5))


def _fold(value: Any) -> str:
    text = str(value or "").strip().upper()
    return "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))


def _number(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _int(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None and number.is_integer() else None


def _normalizar_linha(row: dict[str, str]) -> dict[str, Any]:
    data = str(row.get("data") or "").strip() or None
    return {
        "origem_semantica": "HISTORICO_COMERCIAL_HOMOLOGADO",
        "arquivo_origem": SOURCE_FILE,
        "arquivo_sha256": SOURCE_SHA256,
        "aba_origem": row.get("aba") or None,
        "linha_origem": _int(row.get("linha")),
        "representante_original": row.get("rep_original") or None,
        "representante_atual": row.get("rep_norm") or None,
        "data": data,
        "ano": _int(data[:4]) if data and len(data) >= 4 else None,
        "cliente": row.get("cliente") or None,
        "equipamento": row.get("equipamento") or None,
        "quantidade": _int(row.get("qtd")),
        "valor_unitario": _number(row.get("valor_unit")),
        "valor_total": _number(row.get("valor_total")),
        "previsao": row.get("previsao") or None,
        "probabilidade": _number(row.get("prob")),
        "status": row.get("status") or "INDETERMINADO",
        "motivo_perda": row.get("motivo") or None,
        "observacao": row.get("observacao") or None,
        "canal_venda": row.get("canal") or None,
        "implementadora": row.get("implementadora") or None,
        "flags_validacao": [item for item in str(row.get("flags") or "").split("|") if item],
    }


@lru_cache(maxsize=1)
def carregar_historico_comercial() -> tuple[dict[str, Any], ...]:
    encoded = "".join(part.read_text(encoding="utf-8").strip() for part in PARTS)
    raw = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    rows = tuple(_normalizar_linha(row) for row in csv.DictReader(io.StringIO(raw)))
    if len(rows) != SOURCE_TOTAL:
        raise RuntimeError(f"Fonte histórica homologada inválida: esperado {SOURCE_TOTAL}, recebido {len(rows)}")
    return rows


def _counter(rows: tuple[dict[str, Any], ...], field: str) -> dict[str, int]:
    counts = Counter(str(row.get(field) or "AUSENTE") for row in rows)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def resumir_historico_comercial(rows: tuple[dict[str, Any], ...] | None = None) -> dict[str, Any]:
    base = rows if rows is not None else carregar_historico_comercial()
    return {
        "fonte": SOURCE_FILE,
        "sha256": SOURCE_SHA256,
        "homologado": True,
        "total_registros": len(base),
        "total_unidades": sum(int(row.get("quantidade") or 0) for row in base),
        "valor_nominal": round(sum(float(row.get("valor_total") or 0) for row in base), 2),
        "valor_nominal_nao_e_receita": True,
        "por_aba": _counter(base, "aba_origem"),
        "por_ano": _counter(base, "ano"),
        "por_canal": _counter(base, "canal_venda"),
        "por_status": _counter(base, "status"),
        "por_representante_atual": _counter(base, "representante_atual"),
        "por_equipamento": _counter(base, "equipamento"),
        "por_implementadora": _counter(base, "implementadora"),
        "por_motivo_perda": _counter(base, "motivo_perda"),
        "regra_carla_monica": {
            "registros": sum(1 for row in base if "CARLA" in _fold(row.get("representante_original")) and "MONICA" in _fold(row.get("representante_atual"))),
            "preserva_autoria_historica": True,
        },
    }


def filtrar_historico_comercial(termo: str | None = None, limite: int = 100) -> list[dict[str, Any]]:
    rows = carregar_historico_comercial()
    limite = max(1, min(int(limite or 100), 200))
    if not termo:
        return list(rows[:limite])
    alvo = _fold(termo)
    resultado = []
    for row in rows:
        if alvo in _fold(json.dumps(row, ensure_ascii=False, default=str)):
            resultado.append(row)
            if len(resultado) >= limite:
                break
    return resultado
