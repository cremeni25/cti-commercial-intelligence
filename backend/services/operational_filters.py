from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

VIENA_DDDS = {"011", "012", "013", "014", "015", "018"}


def normalizar_ddd(valor) -> str | None:
    if valor in (None, ""):
        return None
    digitos = "".join(c for c in str(valor) if c.isdigit())
    if not digitos:
        return None
    return digitos[-3:].zfill(3)


def resolver_periodo(periodo: str = "TODO_HISTORICO", inicio: date | None = None, fim: date | None = None):
    hoje = date.today()
    if periodo == "TODO_HISTORICO": return None, None
    if periodo == "HOJE": return hoje, hoje
    if periodo == "ULTIMOS_7_DIAS": return hoje - timedelta(days=6), hoje
    if periodo == "ULTIMOS_30_DIAS": return hoje - timedelta(days=29), hoje
    if periodo == "ULTIMOS_90_DIAS": return hoje - timedelta(days=89), hoje
    if periodo == "MES_ATUAL": return hoje.replace(day=1), hoje
    if periodo == "TRIMESTRE_ATUAL":
        mes = ((hoje.month - 1) // 3) * 3 + 1
        return hoje.replace(month=mes, day=1), hoje
    if periodo == "ANO_ATUAL": return hoje.replace(month=1, day=1), hoje
    return inicio, fim


def data_registro(registro: dict) -> date | None:
    for campo in ("data_venda", "data", "created_at", "updated_at", "data_emissao", "data_pedido"):
        valor = registro.get(campo)
        if not valor:
            continue
        if isinstance(valor, datetime): return valor.date()
        if isinstance(valor, date): return valor
        texto = str(valor).strip()
        for candidato in (texto[:10], texto):
            try: return date.fromisoformat(candidato)
            except ValueError: pass
        for formato in ("%d/%m/%Y", "%d-%m-%Y"):
            try: return datetime.strptime(texto[:10], formato).date()
            except ValueError: pass
    return None


def _registro_viena(origem: str, autorizado: str) -> bool:
    return origem == "VIENA_SP" or autorizado == "VIENA"


def _registro_brasil(origem: str, autorizado: str) -> bool:
    # As planilhas Brasil e Viena são bases independentes. Registros Viena não
    # podem ser somados ao contexto Brasil, mesmo quando compartilham clientes,
    # chassis ou regiões com a base nacional.
    return origem == "BRASIL" and autorizado != "VIENA"


def filtrar_registros(registros: Iterable[dict], contexto: str = "brasil", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None) -> list[dict]:
    uf_normalizada = str(uf).strip().upper() if uf else None
    ddd_normalizado = normalizar_ddd(ddd)
    resultado = []
    for registro in registros or []:
        estado = str(registro.get("estado") or registro.get("uf") or "").strip().upper()
        origem = str(registro.get("origem_base") or "").strip().upper()
        autorizado = str(registro.get("autorizado") or registro.get("dealer") or "").strip().upper()
        registro_ddd = normalizar_ddd(registro.get("ddd") or registro.get("codigo_ddd"))
        pertence_viena = _registro_viena(origem, autorizado)
        pertence_brasil = _registro_brasil(origem, autorizado)

        if contexto == "brasil" and not pertence_brasil: continue
        if contexto == "viena-sp" and not pertence_viena: continue
        if contexto.startswith("uf-") and estado != contexto[3:].upper(): continue
        if contexto.startswith("ddd-"):
            contexto_ddd = normalizar_ddd(contexto[4:])
            if contexto_ddd not in VIENA_DDDS or not pertence_viena or registro_ddd != contexto_ddd: continue
        if uf_normalizada and estado != uf_normalizada: continue
        if ddd_normalizado and registro_ddd != ddd_normalizado: continue

        data = data_registro(registro)
        if inicio and (not data or data < inicio): continue
        if fim and (not data or data > fim): continue
        resultado.append(registro)
    return resultado


def opcoes_contexto(registros: Iterable[dict]) -> dict:
    base = list(registros or [])
    ufs = sorted({str(r.get("estado") or r.get("uf") or "").strip().upper() for r in base if r.get("estado") or r.get("uf")})
    ddds = sorted({d for r in base if (d := normalizar_ddd(r.get("ddd") or r.get("codigo_ddd")))})
    return {"ufs": ufs, "ddds": ddds, "viena_ddds": sorted(VIENA_DDDS)}
