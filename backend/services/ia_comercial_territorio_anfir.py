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

LINHAS_ALIASES = {
    "tr": "TR",
    "trailer": "TR",
    "trailer refrigeration": "TR",
    "dt": "DT",
    "diesel truck": "DT",
    "diesel-truck": "DT",
    "dieseltruck": "DT",
    "dd": "DD",
    "direct drive": "DD",
    "direct-drive": "DD",
    "directdrive": "DD",
}


def _normalizar(valor: Any) -> str:
    return str(valor or "").strip().casefold()


def normalizar_linha(valor: Any) -> str | None:
    texto = _normalizar(valor)
    if not texto:
        return None
    return LINHAS_ALIASES.get(texto, str(valor).strip().upper())


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


def _preenchido(valor: Any) -> bool:
    return bool(str(valor or "").strip())


def _chave_veiculo(item: dict[str, Any]) -> str | None:
    chassi = str(item.get("chassi") or "").strip().upper()
    if chassi:
        return f"chassi:{chassi}"
    placa = str(item.get("placa") or "").strip().upper()
    if placa:
        return f"placa:{placa}"
    id_operacional = str(item.get("id_operacional") or "").strip()
    if id_operacional:
        return f"id_operacional:{id_operacional}"
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
    linha_normalizada = normalizar_linha(linha)
    filtros_texto = {
        "cidade": cidade,
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
        if linha_normalizada and normalizar_linha(item.get("linha")) != linha_normalizada:
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
            if _normalizar(valor) not in _normalizar(item.get(campo)):
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
    chaves_veiculos = {chave for item in registros if (chave := _chave_veiculo(item))}
    return {
        "total_registros": len(registros),
        "total_clientes": len(clientes),
        "total_veiculos_identificaveis": len(chaves_veiculos),
        "registros_sem_identificador_veiculo": sum(1 for item in registros if not _chave_veiculo(item)),
        "valor_total_informado": valor_total,
        "quantidade_total_informada": quantidade_total,
        "cobertura": {
            "com_ddd": sum(1 for item in registros if normalizar_ddd(item.get("ddd"))),
            "sem_ddd": sum(1 for item in registros if not normalizar_ddd(item.get("ddd"))),
            "com_modelo": sum(1 for item in registros if _preenchido(item.get("modelo"))),
            "sem_modelo": sum(1 for item in registros if not _preenchido(item.get("modelo"))),
            "com_placa": sum(1 for item in registros if _preenchido(item.get("placa"))),
            "sem_placa": sum(1 for item in registros if not _preenchido(item.get("placa"))),
            "com_chassi": sum(1 for item in registros if _preenchido(item.get("chassi"))),
            "sem_chassi": sum(1 for item in registros if not _preenchido(item.get("chassi"))),
            "com_numero_frota": sum(1 for item in registros if _preenchido(item.get("numero_frota"))),
            "sem_numero_frota": sum(1 for item in registros if not _preenchido(item.get("numero_frota"))),
            "com_fabricante_caminhao": sum(1 for item in registros if _preenchido(item.get("fabricante_caminhao"))),
            "sem_fabricante_caminhao": sum(1 for item in registros if not _preenchido(item.get("fabricante_caminhao"))),
            "com_modelo_caminhao": sum(1 for item in registros if _preenchido(item.get("modelo_caminhao"))),
            "sem_modelo_caminhao": sum(1 for item in registros if not _preenchido(item.get("modelo_caminhao"))),
        },
        "ranking_ddds": _ranking(registros, "ddd"),
        "ranking_estados": _ranking(registros, "estado"),
        "ranking_cidades": _ranking(registros, "cidade"),
        "ranking_linhas": _ranking(registros, "linha"),
        "ranking_modelos": _ranking(registros, "modelo"),
        "ranking_clientes": _ranking(registros, "cliente"),
        "ranking_implementadoras": _ranking(registros, "implementadora"),
        "ranking_fabricantes_equipamento": _ranking(registros, "fabricante_equipamento"),
        "ranking_tipos_veiculo": _ranking(registros, "tipo_veiculo"),
        "ranking_fabricantes_caminhao": _ranking(registros, "fabricante_caminhao"),
        "ranking_modelos_caminhao": _ranking(registros, "modelo_caminhao"),
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
        "linha": normalizar_linha(item.get("linha")),
        "modelo": item.get("modelo"),
        "placa": item.get("placa"),
        "chassi": item.get("chassi"),
        "numero_frota": item.get("numero_frota"),
        "fabricante_caminhao": item.get("fabricante_caminhao"),
        "modelo_caminhao": item.get("modelo_caminhao"),
        "eixo": item.get("eixo"),
        "tipo_veiculo": item.get("tipo_veiculo"),
        "fabricante_equipamento": item.get("fabricante_equipamento"),
        "implementadora": item.get("implementadora"),
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
    periodo_normalizado = str(periodo or "TODO_HISTORICO").upper()

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

    filtros_comuns = {
        "ddd": ddd,
        "uf": uf,
        "cidade": cidade,
        "linha": linha,
        "modelo": modelo,
        "cliente": cliente,
        "implementadora": implementadora,
        "fabricante_equipamento": fabricante_equipamento,
        "origem": origem,
        "termo": termo,
    }
    filtrados = _filtrar(
        base_autorizada,
        periodo=periodo_normalizado,
        inicio=inicio,
        fim=fim,
        **filtros_comuns,
    )

    historico_mesmo_recorte = filtrados
    if periodo_normalizado != "TODO_HISTORICO" or inicio or fim:
        historico_mesmo_recorte = _filtrar(
            base_autorizada,
            periodo="TODO_HISTORICO",
            inicio=None,
            fim=None,
            **filtros_comuns,
        )

    total = len(filtrados)
    pagina = filtrados[offset : offset + limite]
    linha_normalizada = normalizar_linha(linha)
    resumo_historico_disponivel = _resumir(historico_mesmo_recorte)

    return {
        "fonte": "cti_anfir",
        "escopo": escopo,
        "filtros_aplicados": {
            "ddd": normalizar_ddd(ddd),
            "uf": str(uf or "").strip().upper() or None,
            "cidade": cidade,
            "periodo": periodo_normalizado,
            "inicio": inicio,
            "fim": fim,
            "linha": linha_normalizada,
            "linha_recebida": linha,
            "modelo": modelo,
            "cliente": cliente,
            "implementadora": implementadora,
            "fabricante_equipamento": fabricante_equipamento,
            "origem": origem,
            "termo": termo,
        },
        "resumo": _resumir(filtrados),
        "resumo_historico_disponivel": resumo_historico_disponivel,
        "total_historico_disponivel": len(historico_mesmo_recorte),
        "total_encontrado": total,
        "offset": offset,
        "limite": limite,
        "tem_mais": offset + len(pagina) < total,
        "resultado": [_registro_publico(item) for item in pagina],
        "observacao": (
            "Contagens e rankings de resumo usam todo o recorte temporal solicitado; resultado é a página detalhada. "
            "total_veiculos_identificaveis deduplica registros por chassi, depois placa e depois id_operacional; total_registros não deve ser interpretado automaticamente como quantidade de veículos únicos. "
            "Quando há período específico, resumo_historico_disponivel mostra o mesmo recorte sem filtro temporal. "
            "Zero no período não equivale a zero histórico."
        ),
    }


def consultar_territorio_semantico(usuario_id: str, tipo_usuario: str, **filtros: Any) -> dict[str, Any]:
    resultado = _consultar(usuario_id, tipo_usuario, **filtros)
    resultado["visao"] = "territorio"
    return resultado


def consultar_anfir_semantico(usuario_id: str, tipo_usuario: str, **filtros: Any) -> dict[str, Any]:
    resultado = _consultar(usuario_id, tipo_usuario, **filtros)
    resultado["visao"] = "anfir_historico"
    return resultado
