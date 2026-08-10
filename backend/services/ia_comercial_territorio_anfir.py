from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from repositories.cti_repository import repository
from services.ia_comercial_cti import _consulta_segura
from services.operational_filters import data_registro, normalizar_ddd, resolver_periodo

PAPEIS_GLOBAIS = {
    "ADMIN_MASTER",
    "CEO",
    "DIRETOR_ADMINISTRATIVO",
    "GERENTE_NACIONAL",
    "GERENTE_LATAM",
}


def _normalizar(valor: Any) -> str:
    return str(valor or "").strip().casefold()


def _numero(valor: Any) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _data_iso(valor: Any) -> date | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    try:
        return date.fromisoformat(texto[:10])
    except ValueError:
        return None


def _usuario_por_id(usuario_id: str) -> dict[str, Any] | None:
    for item in _consulta_segura("cti_users"):
        if str(item.get("id") or "") == str(usuario_id):
            return item
    return None


def _ddds_por_territorios(usuario_id: str) -> set[str]:
    vinculos = [
        item
        for item in _consulta_segura("cti_usuario_territorio")
        if str(item.get("usuario_id") or "") == str(usuario_id)
    ]
    territorio_ids = {
        str(item.get("territorio_id"))
        for item in vinculos
        if item.get("territorio_id")
    }
    if not territorio_ids:
        return set()

    ddds: set[str] = set()
    for item in _consulta_segura("cti_territorio_cidades"):
        if str(item.get("territorio_id") or "") not in territorio_ids:
            continue
        ddd = normalizar_ddd(item.get("ddd"))
        if ddd:
            ddds.add(ddd)
    return ddds


def resolver_escopo_territorial(usuario_id: str, tipo_usuario: str) -> dict[str, Any]:
    papel = str(tipo_usuario or "").strip().upper()
    if papel in PAPEIS_GLOBAIS:
        return {
            "modo": "global",
            "papel": papel,
            "ddds_autorizados": None,
            "territorio": None,
        }

    usuario = _usuario_por_id(usuario_id) or {}
    ddds_diretos = {
        ddd
        for valor in (usuario.get("ddds") or [])
        if (ddd := normalizar_ddd(valor))
    }
    ddds = ddds_diretos or _ddds_por_territorios(usuario_id)

    return {
        "modo": "territorial" if ddds else "sem_territorio_configurado",
        "papel": papel,
        "ddds_autorizados": sorted(ddds),
        "territorio": usuario.get("territorio"),
    }


def _aplicar_rbac(
    registros: list[dict[str, Any]],
    usuario_id: str,
    tipo_usuario: str,
    ddd_solicitado: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], str | None]:
    escopo = resolver_escopo_territorial(usuario_id, tipo_usuario)
    permitido = escopo.get("ddds_autorizados")
    ddd = normalizar_ddd(ddd_solicitado)

    if permitido is None:
        return registros, escopo, None
    if not permitido:
        return [], escopo, "Usuário sem território/DDD configurado para consulta territorial."
    if ddd and ddd not in set(permitido):
        return [], escopo, "DDD solicitado fora do escopo autorizado do usuário."

    autorizados = set(permitido)
    filtrados = [
        item
        for item in registros
        if normalizar_ddd(item.get("ddd") or item.get("codigo_ddd")) in autorizados
    ]
    return filtrados, escopo, None


def _filtrar(
    registros: list[dict[str, Any]],
    *,
    ddd: str | None = None,
    uf: str | None = None,
    cidade: str | None = None,
    periodo: str = "TODO_HISTORICO",
    inicio: str | None = None,
    fim: str | None = None,
    linha: str | None = None,
    modelo: str | None = None,
    cliente: str | None = None,
    implementadora: str | None = None,
    fabricante_equipamento: str | None = None,
    origem: str | None = None,
    termo: str | None = None,
) -> list[dict[str, Any]]:
    inicio_data, fim_data = resolver_periodo(
        str(periodo or "TODO_HISTORICO").upper(),
        _data_iso(inicio),
        _data_iso(fim),
    )
    ddd_normalizado = normalizar_ddd(ddd)
    uf_normalizada = str(uf or "").strip().upper() or None
    filtros_texto = {
        "cidade": cidade,
        "linha": linha,
        "modelo": modelo,
        "cliente": cliente,
        "implementadora": implementadora,
        "fabricante_equipamento": fabricante_equipamento,
    }
    resultado: list[dict[str, Any]] = []
    for item in registros:
        if ddd_normalizado and normalizar_ddd(item.get("ddd") or item.get("codigo_ddd")) != ddd_normalizado:
            continue
        estado = str(item.get("estado") or item.get("uf") or "").strip().upper()
        if uf_normalizada and estado != uf_normalizada:
            continue
        data = data_registro(item)
        if inicio_data and (not data or data < inicio_data):
            continue
        if fim_data and (not data or data > fim_data):
            continue
        rejeitado = False
        for campo, valor in filtros_texto.items():
            if not valor:
                continue
            campo_real = "implementadora" if campo == "implementadora" else campo
            if _normalizar(valor) not in _normalizar(item.get(campo_real)):
                rejeitado = True
                break
        if rejeitado:
            continue
        if origem:
            origem_item = item.get("origem_base") or item.get("origem_dado")
            if _normalizar(origem) not in _normalizar(origem_item):
                continue
        if termo and _normalizar(termo) not in _normalizar(json.dumps(item, ensure_ascii=False, default=str)):
            continue
        resultado.append(item)
    return resultado


def _ranking(registros: list[dict[str, Any]], campo: str, limite: int = 15) -> list[dict[str, Any]]:
    contador = Counter()
    for item in registros:
        valor = item.get(campo)
        if campo == "ddd":
            valor = normalizar_ddd(valor)
        texto = str(valor or "").strip()
        if texto:
            contador[texto] += 1
    return [
        {"valor": valor, "registros": quantidade}
        for valor, quantidade in contador.most_common(limite)
    ]


def _resumir(registros: list[dict[str, Any]]) -> dict[str, Any]:
    clientes = {str(item.get("cliente") or "").strip() for item in registros if item.get("cliente")}
    valor_total = round(sum(_numero(item.get("valor")) for item in registros), 2)
    quantidade_total = round(sum(_numero(item.get("quantidade")) for item in registros), 2)
    return {
        "total_registros": len(registros),
        "total_clientes": len(clientes),
        "valor_total_informado": valor_total,
        "quantidade_total_informada": quantidade_total,
        "cobertura": {
            "com_ddd": sum(1 for item in registros if normalizar_ddd(item.get("ddd"))),
            "sem_ddd": sum(1 for item in registros if not normalizar_ddd(item.get("ddd"))),
            "com_modelo": sum(1 for item in registros if str(item.get("modelo") or "").strip()),
            "sem_modelo": sum(1 for item in registros if not str(item.get("modelo") or "").strip()),
        },
        "ranking_ddds": _ranking(registros, "ddd"),
        "ranking_estados": _ranking(registros, "estado"),
        "ranking_cidades": _ranking(registros, "cidade"),
        "ranking_linhas": _ranking(registros, "linha"),
        "ranking_modelos": _ranking(registros, "modelo"),
        "ranking_clientes": _ranking(registros, "cliente"),
        "ranking_implementadoras": _ranking(registros, "implementadora"),
        "ranking_fabricantes_equipamento": _ranking(registros, "fabricante_equipamento"),
    }


def _registro_publico(item: dict[str, Any]) -> dict[str, Any]:
    data = data_registro(item)
    return {
        "data": data.isoformat() if data else None,
        "cliente": item.get("cliente"),
        "cidade": item.get("cidade"),
        "estado": item.get("estado"),
        "ddd": normalizar_ddd(item.get("ddd")),
        "regiao": item.get("regiao"),
        "sub_regiao": item.get("sub_regiao"),
        "linha": item.get("linha"),
        "modelo": item.get("modelo"),
        "fabricante_equipamento": item.get("fabricante_equipamento"),
        "implementadora": item.get("implementadora"),
        "tipo_veiculo": item.get("tipo_veiculo"),
        "status": item.get("status"),
        "valor": item.get("valor"),
        "quantidade": item.get("quantidade"),
        "origem_base": item.get("origem_base"),
        "origem_dado": item.get("origem_dado"),
    }


def _consultar(
    usuario_id: str,
    tipo_usuario: str,
    *,
    ddd: str | None = None,
    uf: str | None = None,
    cidade: str | None = None,
    periodo: str = "TODO_HISTORICO",
    inicio: str | None = None,
    fim: str | None = None,
    linha: str | None = None,
    modelo: str | None = None,
    cliente: str | None = None,
    implementadora: str | None = None,
    fabricante_equipamento: str | None = None,
    origem: str | None = None,
    termo: str | None = None,
    limite: int = 30,
    offset: int = 0,
) -> dict[str, Any]:
    limite = max(1, min(int(limite or 30), 100))
    offset = max(0, int(offset or 0))
    try:
        base = list(repository.buscar_cti_anfir() or [])
    except Exception:
        base = []

    base_autorizada, escopo, erro_rbac = _aplicar_rbac(base, usuario_id, tipo_usuario, ddd)
    if erro_rbac:
        return {
            "erro": erro_rbac,
            "escopo": escopo,
            "total_encontrado": 0,
            "resultado": [],
        }

    filtrados = _filtrar(
        base_autorizada,
        ddd=ddd,
        uf=uf,
        cidade=cidade,
        periodo=periodo,
        inicio=inicio,
        fim=fim,
        linha=linha,
        modelo=modelo,
        cliente=cliente,
        implementadora=implementadora,
        fabricante_equipamento=fabricante_equipamento,
        origem=origem,
        termo=termo,
    )
    total = len(filtrados)
    pagina = filtrados[offset : offset + limite]
    return {
        "fonte": "cti_anfir",
        "escopo": escopo,
        "filtros_aplicados": {
            "ddd": normalizar_ddd(ddd),
            "uf": str(uf or "").strip().upper() or None,
            "cidade": cidade,
            "periodo": periodo,
            "inicio": inicio,
            "fim": fim,
            "linha": linha,
            "modelo": modelo,
            "cliente": cliente,
            "implementadora": implementadora,
            "fabricante_equipamento": fabricante_equipamento,
            "origem": origem,
            "termo": termo,
        },
        "resumo": _resumir(filtrados),
        "total_encontrado": total,
        "offset": offset,
        "limite": limite,
        "tem_mais": offset + len(pagina) < total,
        "resultado": [_registro_publico(item) for item in pagina],
        "observacao": "Contagens e rankings usam todo o recorte autorizado; resultado é a página detalhada solicitada.",
    }


def consultar_territorio_semantico(usuario_id: str, tipo_usuario: str, **filtros: Any) -> dict[str, Any]:
    resultado = _consultar(usuario_id, tipo_usuario, **filtros)
    resultado["visao"] = "territorio"
    return resultado


def consultar_anfir_semantico(usuario_id: str, tipo_usuario: str, **filtros: Any) -> dict[str, Any]:
    resultado = _consultar(usuario_id, tipo_usuario, **filtros)
    resultado["visao"] = "anfir_historico"
    return resultado
