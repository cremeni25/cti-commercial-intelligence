from collections import Counter
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from repositories.cti_repository import repository
from services.base_analytics import valor_float
from services.operational_filters import filtrar_registros

router = APIRouter(prefix="/modulos", tags=["Módulos CTI"])

EQUIPAMENTOS = {
    "trailer": {"nome": "TR • Trailer", "termos": ("TRAILER", "VECTOR", "X4")},
    "diesel-truck": {"nome": "DT • Diesel Truck", "termos": ("DIESEL", "SUPRA")},
    "direct-drive": {"nome": "DD • Direct Drive", "termos": ("DIRECT", "CITIMAX", "XARIOS", "D6", "D7")},
}


def _todos_registros(contexto="brasil", uf=None, ddd=None, inicio=None, fim=None):
    return filtrar_registros(repository.buscar_cti_anfir(), contexto=contexto, uf=uf, ddd=ddd, inicio=inicio, fim=fim)


def _texto_registro(registro):
    return " ".join(str(registro.get(campo) or "") for campo in ("linha", "modelo", "tipo_veiculo", "fabricante_equipamento")).upper()


CAMPOS_EMPRESA = ("empresa", "cliente", "transportadora", "razao_social", "razão social", "nome_cliente")


def _nome_empresa(registro):
    for campo in CAMPOS_EMPRESA:
        valor = registro.get(campo)
        if valor: return str(valor).strip()
    return ""


def _consolidar_empresas(contexto="brasil", uf=None, ddd=None, inicio=None, fim=None):
    registros = [r for r in _todos_registros(contexto, uf, ddd, inicio, fim) if _nome_empresa(r)]
    agrupado = {}
    for registro in registros:
        nome = _nome_empresa(registro)
        item = agrupado.setdefault(nome, {"nome": nome, "quantidade_registros": 0, "valor_total": 0, "estados": set(), "municipios": set(), "linhas": set(), "status": Counter()})
        item["quantidade_registros"] += 1; item["valor_total"] += valor_float(registro.get("valor"))
        if registro.get("estado"): item["estados"].add(registro.get("estado"))
        if registro.get("cidade"): item["municipios"].add(registro.get("cidade"))
        if registro.get("linha"): item["linhas"].add(registro.get("linha"))
        item["status"][registro.get("status") or "OUTROS"] += 1
    resultado = []
    for item in agrupado.values():
        item["valor_total"] = round(item["valor_total"], 2); item["estados"] = sorted(item["estados"]); item["municipios"] = sorted(item["municipios"]); item["linhas"] = sorted(item["linhas"]); item["status"] = dict(item["status"]); resultado.append(item)
    return sorted(resultado, key=lambda item: item["quantidade_registros"], reverse=True)


@router.get("/empresas")
def listar_empresas(contexto: str = "brasil", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    return _consolidar_empresas(contexto, uf, ddd, inicio, fim)


@router.get("/transportadoras")
def listar_transportadoras(contexto: str = "brasil", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    return _consolidar_empresas(contexto, uf, ddd, inicio, fim)


@router.get("/equipamentos/{slug}")
def detalhe_equipamento(slug: str, contexto: str = "brasil", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    config = EQUIPAMENTOS.get(slug)
    if not config: raise HTTPException(status_code=404, detail="Equipamento não configurado")
    registros = [r for r in _todos_registros(contexto, uf, ddd, inicio, fim) if any(t in _texto_registro(r) for t in config["termos"])]
    estados = Counter(r.get("estado") for r in registros if r.get("estado")); implementadoras = Counter(r.get("implementadora") for r in registros if r.get("implementadora")); linhas = Counter(r.get("linha") for r in registros if r.get("linha")); empresas = Counter(_nome_empresa(r) for r in registros if _nome_empresa(r)); valor_total = sum(valor_float(r.get("valor")) for r in registros)
    return {
        "slug": slug, "nome": config["nome"], "total_registros": len(registros), "valor_total": round(valor_total, 2),
        "metadata": {"contexto": contexto, "uf": uf, "ddd": ddd, "inicio": inicio.isoformat() if inicio else None, "fim": fim.isoformat() if fim else None},
        "estados": [{"nome": n, "quantidade_registros": q} for n, q in estados.most_common()],
        "implementadoras": [{"nome": n, "quantidade_registros": q} for n, q in implementadoras.most_common()],
        "linhas": [{"nome": n, "quantidade_registros": q} for n, q in linhas.most_common()],
        "empresas": [{"nome": n, "quantidade_registros": q} for n, q in empresas.most_common(20)],
    }
