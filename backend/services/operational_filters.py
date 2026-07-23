from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

VIENA_DDDS = {"011", "012", "013", "014", "015", "018"}


def normalizar_ddd(valor) -> str | None:
    if valor in (None, ""):
        return None
    digitos = "".join(c for c in str(valor) if c.isdigit())
    if not digitos:
        return None
    return digitos[-3:].zfill(3)


def data_registro(registro: dict) -> date | None:
    for campo in ("data_venda", "data", "created_at", "updated_at", "data_emissao", "data_pedido"):
        valor = registro.get(campo)
        if not valor:
            continue
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        texto = str(valor).strip()
        for candidato in (texto[:10], texto):
            try:
                return date.fromisoformat(candidato)
            except ValueError:
                pass
        for formato in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(texto[:10], formato).date()
            except ValueError:
                pass
    return None


def filtrar_registros(
    registros: Iterable[dict],
    contexto: str = "brasil",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[dict]:
    uf_normalizada = str(uf).strip().upper() if uf else None
    ddd_normalizado = normalizar_ddd(ddd)
    resultado = []

    for registro in registros or []:
        estado = str(registro.get("estado") or registro.get("uf") or "").strip().upper()
        origem = str(registro.get("origem_base") or "").strip().upper()
        autorizado = str(registro.get("autorizado") or registro.get("dealer") or "").strip().upper()
        registro_ddd = normalizar_ddd(registro.get("ddd") or registro.get("codigo_ddd"))

        if contexto == "viena-sp" and not (origem == "VIENA_SP" or autorizado == "VIENA"):
            continue
        if contexto.startswith("uf-") and estado != contexto[3:].upper():
            continue
        if contexto.startswith("ddd-") and registro_ddd != normalizar_ddd(contexto[4:]):
            continue
        if uf_normalizada and estado != uf_normalizada:
            continue
        if ddd_normalizado and registro_ddd != ddd_normalizado:
            continue

        data = data_registro(registro)
        if inicio and (not data or data < inicio):
            continue
        if fim and (not data or data > fim):
            continue
        resultado.append(registro)

    return resultado


def opcoes_contexto(registros: Iterable[dict]) -> dict:
    ufs = sorted({str(r.get("estado") or r.get("uf") or "").strip().upper() for r in registros or [] if r.get("estado") or r.get("uf")})
    ddds = sorted({d for r in registros or [] if (d := normalizar_ddd(r.get("ddd") or r.get("codigo_ddd")))})
    return {
        "ufs": ufs,
        "ddds": ddds,
        "viena_ddds": sorted(VIENA_DDDS),
    }
