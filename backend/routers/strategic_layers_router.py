from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase
from services.anfir_read_cache import fonte_anfir, preaquecer_anfir_async
from services.base_analytics import valor_float
from services.crm_live_projection import carregar_oportunidades_enriquecidas, equipamentos_registro, familias_registro
from services.historical_commercial_source import carregar_historico_comercial
from services.operational_filters import filtrar_registros, resolver_periodo

router = APIRouter(prefix="/estrategia", tags=["Estratégia CTI"])

# Carrega a base ANFIR em segundo plano no backend de produção. Isso evita que
# o primeiro usuário do Dashboard pague o custo integral da paginação da fonte.
preaquecer_anfir_async()

EQUIPAMENTOS = {
    "trailer": {"nome": "TR • Trailer", "termos": ("TRAILER", "VECTOR", "X4")},
    "diesel-truck": {"nome": "DT • Diesel Truck", "termos": ("DIESEL", "SUPRA")},
    "direct-drive": {"nome": "DD • Direct Drive", "termos": ("DIRECT", "CITIMAX", "XARIOS", "D6", "D7")},
}

CODIGOS_FAMILIA = {
    "TR": "trailer",
    "DT": "diesel-truck",
    "DD": "direct-drive",
}


def _texto(*valores: Any) -> str:
    return " ".join(str(valor or "") for valor in valores).upper()


def _codigo_familia(valor: Any) -> str | None:
    texto = str(valor or "").strip().upper().replace("•", "-")
    if not texto:
        return None
    prefixo = texto.split("-", 1)[0].strip().split(" ", 1)[0].strip()
    return CODIGOS_FAMILIA.get(prefixo)


def _combina(texto: str, termos: tuple[str, ...]) -> bool:
    return any(termo in texto for termo in termos)


def _ranking(counter: Counter, limite: int = 20) -> list[dict[str, Any]]:
    return [
        {"nome": str(nome), "quantidade_registros": quantidade}
        for nome, quantidade in counter.most_common(limite)
        if nome not in (None, "")
    ]


def _lista_segura(tabela: str) -> list[dict[str, Any]]:
    try:
        return supabase.table(tabela).select("*").execute().data or []
    except Exception:
        return []


def _data_no_intervalo(valor: Any, inicio: date | None, fim: date | None) -> bool:
    if not valor or (inicio is None and fim is None):
        return True
    try:
        atual = date.fromisoformat(str(valor)[:10])
    except ValueError:
        return True
    if inicio and atual < inicio:
        return False
    if fim and atual > fim:
        return False
    return True


def _anfir(contexto: str, periodo: str, uf: str | None, ddd: str | None, inicio: date | None, fim: date | None):
    inicio_efetivo, fim_efetivo = resolver_periodo(periodo, inicio, fim)
    registros = filtrar_registros(
        fonte_anfir(),
        contexto=contexto,
        uf=uf,
        ddd=ddd,
        inicio=inicio_efetivo,
        fim=fim_efetivo,
    )
    return registros, inicio_efetivo, fim_efetivo


def _familia_registro_anfir(registro: dict[str, Any]) -> str | None:
    por_codigo = _codigo_familia(registro.get("linha"))
    if por_codigo:
        return por_codigo
    texto = _texto(
        registro.get("linha"), registro.get("modelo"), registro.get("tipo_veiculo"),
        registro.get("fabricante_equipamento"), registro.get("produto"),
    )
    for slug, config in EQUIPAMENTOS.items():
        if _combina(texto, config["termos"]):
            return slug
    return None


def _familia_historico(registro: dict[str, Any]) -> str | None:
    texto = _texto(registro.get("equipamento"))
    for slug, config in EQUIPAMENTOS.items():
        if _combina(texto, config["termos"]):
            return slug
    return None


def _familias_crm(registro: dict[str, Any]) -> list[str]:
    familias = familias_registro(registro)
    if familias:
        return familias
    por_codigo = _codigo_familia(registro.get("linha_equipamentos"))
    if por_codigo:
        return [por_codigo]
    texto = _texto(
        registro.get("linha_equipamentos"), registro.get("equipamento"), registro.get("titulo"), registro.get("descricao")
    )
    return [slug for slug, config in EQUIPAMENTOS.items() if _combina(texto, config["termos"])]


def _familia_crm(registro: dict[str, Any]) -> str | None:
    familias = _familias_crm(registro)
    return familias[0] if familias else None


def _camada_anfir(registros: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "origem": "CTI_ANFIR",
        "semantica": "REALIZADO",
        "total_registros": len(registros),
        "valor_total": round(sum(valor_float(item.get("valor")) for item in registros), 2),
        "estados": _ranking(Counter(item.get("estado") or item.get("uf") for item in registros)),
        "municipios": _ranking(Counter(item.get("cidade") or item.get("municipio") for item in registros)),
        "ddds": _ranking(Counter(item.get("ddd") for item in registros)),
        "implementadoras": _ranking(Counter(item.get("implementadora") or item.get("implementador") for item in registros)),
        "empresas": _ranking(Counter(item.get("cliente") or item.get("empresa") or item.get("transportadora") for item in registros)),
        "equipamentos": _ranking(Counter(item.get("modelo") or item.get("linha") or item.get("produto") for item in registros)),
    }


def _camada_historico(registros: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "origem": "HISTORICO_COMERCIAL_2023_2026",
        "semantica": "CONSULTA_HISTORICA",
        "total_registros": len(registros),
        "total_unidades": sum(int(item.get("quantidade") or 0) for item in registros),
        "valor_nominal": round(sum(valor_float(item.get("valor_total")) for item in registros), 2),
        "equipamentos": _ranking(Counter(item.get("equipamento") for item in registros)),
        "implementadoras": _ranking(Counter(item.get("implementadora") for item in registros)),
        "empresas": _ranking(Counter(item.get("cliente") for item in registros)),
        "status": _ranking(Counter(item.get("status") for item in registros)),
        "nota_territorial": "A fonte histórica preserva cliente/equipamento/implementadora, mas não possui geografia própria por registro; não é fundida artificialmente ao ANFIR.",
    }


def _camada_crm(registros: list[dict[str, Any]]) -> dict[str, Any]:
    fechados = {"GANHO", "PERDIDO", "CANCELADO", "CANCELADA", "CONCLUIDO", "CONCLUIDA"}
    ativos = [item for item in registros if str(item.get("status") or "").upper() not in fechados]
    equipamentos_counter: Counter[str] = Counter()
    for item in ativos:
        for equipamento in equipamentos_registro(item):
            equipamentos_counter[equipamento] += 1
    return {
        "origem": "CRM",
        "semantica": "EM_CURSO",
        "total_registros": len(ativos),
        "valor_pipeline": round(sum(valor_float(item.get("valor_estimado")) for item in ativos), 2),
        "estados": _ranking(Counter(item.get("estado") for item in ativos)),
        "municipios": _ranking(Counter(item.get("municipio") for item in ativos)),
        "ddds": _ranking(Counter(item.get("ddd") for item in ativos)),
        "equipamentos": _ranking(equipamentos_counter),
        "status": _ranking(Counter(item.get("status") for item in ativos)),
    }


@router.get("/equipamentos/{slug}")
def equipamento_estrategico(
    slug: str,
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
):
    config = EQUIPAMENTOS.get(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Equipamento não configurado")

    anf_base, inicio_efetivo, fim_efetivo = _anfir(contexto, periodo, uf, ddd, inicio, fim)
    anf_registros = [item for item in anf_base if _familia_registro_anfir(item) == slug]

    hist_registros = [
        item for item in carregar_historico_comercial()
        if _familia_historico(item) == slug and _data_no_intervalo(item.get("data"), inicio_efetivo, fim_efetivo)
    ]

    crm_registros = [item for item in carregar_oportunidades_enriquecidas() if slug in _familias_crm(item)]

    return {
        "slug": slug,
        "nome": config["nome"],
        "regra": "CAMADAS_SEPARADAS_SEM_FUSAO",
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "uf": uf,
            "ddd": ddd,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
        },
        "realizado": _camada_anfir(anf_registros),
        "historico_comercial": _camada_historico(hist_registros),
        "em_curso": _camada_crm(crm_registros),
    }


@router.get("/mapa")
def mapa_estrategico(
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
):
    anf_base, inicio_efetivo, fim_efetivo = _anfir(contexto, periodo, uf, ddd, inicio, fim)
    historico = [
        item for item in carregar_historico_comercial()
        if _data_no_intervalo(item.get("data"), inicio_efetivo, fim_efetivo)
    ]
    crm = carregar_oportunidades_enriquecidas()

    familias_anfir = Counter(_familia_registro_anfir(item) for item in anf_base)
    familias_hist = Counter(_familia_historico(item) for item in historico)
    familias_crm: Counter[str] = Counter()
    for item in crm:
        for familia in _familias_crm(item):
            familias_crm[familia] += 1

    def familias(counter: Counter) -> list[dict[str, Any]]:
        return [
            {"nome": EQUIPAMENTOS[slug]["nome"], "quantidade_registros": counter.get(slug, 0)}
            for slug in EQUIPAMENTOS
        ]

    realizado = _camada_anfir(anf_base)
    realizado["familias"] = familias(familias_anfir)
    historico_cam = _camada_historico(historico)
    historico_cam["familias"] = familias(familias_hist)
    em_curso = _camada_crm(crm)
    em_curso["familias"] = familias(familias_crm)

    return {
        "regra": "CORRELACAO_SEM_FUSAO",
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "uf": uf,
            "ddd": ddd,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
        },
        "realizado": realizado,
        "historico_comercial": historico_cam,
        "em_curso": em_curso,
    }
