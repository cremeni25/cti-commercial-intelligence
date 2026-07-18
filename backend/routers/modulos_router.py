from collections import Counter

from fastapi import APIRouter, HTTPException, Query

from repositories.cti_repository import repository
from services.base_analytics import valor_float

router = APIRouter(prefix="/modulos", tags=["Módulos CTI"])

EQUIPAMENTOS = {
    "trailer": {
        "nome": "TR • Trailer",
        "termos": ("TRAILER", "VECTOR", "X4"),
    },
    "diesel-truck": {
        "nome": "DT • Diesel Truck",
        "termos": ("DIESEL", "SUPRA"),
    },
    "direct-drive": {
        "nome": "DD • Direct Drive",
        "termos": ("DIRECT", "CITIMAX", "XARIOS", "D6", "D7"),
    },
}


def _todos_registros(contexto: str = "brasil"):
    registros = repository.buscar_cti_anfir()
    if contexto == "viena-sp":
        return [
            registro
            for registro in registros
            if registro.get("origem_base") == "VIENA_SP"
            and (registro.get("autorizado") in (None, "VIENA"))
        ]
    return registros


def _contexto_param(contexto: str = Query("brasil", pattern="^(brasil|viena-sp)$")):
    return contexto


def _texto_registro(registro):
    return " ".join(
        str(registro.get(campo) or "")
        for campo in ("linha", "modelo", "tipo_veiculo", "fabricante_equipamento")
    ).upper()


CAMPOS_EMPRESA = ("empresa", "cliente", "transportadora", "razao_social", "razão social", "nome_cliente")


def _nome_empresa(registro):
    for campo in CAMPOS_EMPRESA:
        valor = registro.get(campo)
        if valor:
            return str(valor).strip()
    return ""


def _consolidar_empresas(contexto: str = "brasil"):
    registros = [r for r in _todos_registros(contexto) if _nome_empresa(r)]
    agrupado = {}

    for registro in registros:
        nome = _nome_empresa(registro)
        if not nome:
            continue

        item = agrupado.setdefault(
            nome,
            {
                "nome": nome,
                "quantidade_registros": 0,
                "valor_total": 0,
                "estados": set(),
                "municipios": set(),
                "linhas": set(),
                "status": Counter(),
            },
        )
        item["quantidade_registros"] += 1
        item["valor_total"] += valor_float(registro.get("valor"))
        if registro.get("estado"):
            item["estados"].add(registro.get("estado"))
        if registro.get("cidade"):
            item["municipios"].add(registro.get("cidade"))
        if registro.get("linha"):
            item["linhas"].add(registro.get("linha"))
        item["status"][registro.get("status") or "OUTROS"] += 1

    resultado = []
    for item in agrupado.values():
        item["valor_total"] = round(item["valor_total"], 2)
        item["estados"] = sorted(item["estados"])
        item["municipios"] = sorted(item["municipios"])
        item["linhas"] = sorted(item["linhas"])
        item["status"] = dict(item["status"])
        resultado.append(item)

    return sorted(resultado, key=lambda item: item["quantidade_registros"], reverse=True)


@router.get("/empresas")
def listar_empresas(contexto: str = Query("brasil", pattern="^(brasil|viena-sp)$")):
    return _consolidar_empresas(contexto)


@router.get("/transportadoras")
def listar_transportadoras(contexto: str = Query("brasil", pattern="^(brasil|viena-sp)$")):
    return _consolidar_empresas(contexto)


@router.get("/equipamentos/{slug}")
def detalhe_equipamento(slug: str, contexto: str = Query("brasil", pattern="^(brasil|viena-sp)$")):
    config = EQUIPAMENTOS.get(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Equipamento não configurado")

    termos = config["termos"]
    registros = [
        registro
        for registro in _todos_registros(contexto)
        if any(termo in _texto_registro(registro) for termo in termos)
    ]

    estados = Counter(r.get("estado") for r in registros if r.get("estado"))
    implementadoras = Counter(
        r.get("implementadora") for r in registros if r.get("implementadora")
    )
    linhas = Counter(r.get("linha") for r in registros if r.get("linha"))
    empresas = Counter(_nome_empresa(r) for r in registros if _nome_empresa(r))
    valor_total = sum(valor_float(r.get("valor")) for r in registros)

    return {
        "slug": slug,
        "nome": config["nome"],
        "total_registros": len(registros),
        "valor_total": round(valor_total, 2),
        "estados": [
            {"nome": nome, "quantidade_registros": qtd}
            for nome, qtd in estados.most_common()
        ],
        "implementadoras": [
            {"nome": nome, "quantidade_registros": qtd}
            for nome, qtd in implementadoras.most_common()
        ],
        "linhas": [
            {"nome": nome, "quantidade_registros": qtd}
            for nome, qtd in linhas.most_common()
        ],
        "empresas": [
            {"nome": nome, "quantidade_registros": qtd}
            for nome, qtd in empresas.most_common(20)
        ],
    }
