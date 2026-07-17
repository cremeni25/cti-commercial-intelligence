from collections import Counter

from fastapi import APIRouter, HTTPException

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


def _todos_registros():
    return repository.buscar_cti_anfir()


def _texto_registro(registro):
    return " ".join(
        str(registro.get(campo) or "")
        for campo in ("linha", "modelo", "tipo_veiculo", "fabricante_equipamento")
    ).upper()


@router.get("/transportadoras")
def listar_transportadoras():
    registros = [r for r in _todos_registros() if r.get("cliente")]
    agrupado = {}

    for registro in registros:
        nome = str(registro.get("cliente") or "").strip()
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


@router.get("/equipamentos/{slug}")
def detalhe_equipamento(slug: str):
    config = EQUIPAMENTOS.get(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Equipamento não configurado")

    termos = config["termos"]
    registros = [
        registro
        for registro in _todos_registros()
        if any(termo in _texto_registro(registro) for termo in termos)
    ]

    estados = Counter(r.get("estado") for r in registros if r.get("estado"))
    implementadoras = Counter(
        r.get("implementadora") for r in registros if r.get("implementadora")
    )
    linhas = Counter(r.get("linha") for r in registros if r.get("linha"))
    clientes = Counter(r.get("cliente") for r in registros if r.get("cliente"))
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
        "clientes": [
            {"nome": nome, "quantidade_registros": qtd}
            for nome, qtd in clientes.most_common(20)
        ],
    }
