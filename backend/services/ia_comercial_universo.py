from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from repositories.cti_repository import repository
from services.historical_commercial_source import carregar_historico_comercial
from services.ia_comercial_cti import _consulta_segura
from services.ia_comercial_dados_semanticos import _escopo_autorizado
from services.ia_comercial_territorio_anfir import _aplicar_rbac, resolver_escopo_territorial
from services.product_catalog_service import listar_catalogo


CAMPOS_SENSIVEIS = {
    "password", "senha", "password_hash", "senha_hash", "token", "access_token",
    "refresh_token", "secret", "client_secret", "api_key", "apikey",
}

FONTES_PUBLICAS = {
    "historico_anfir": "Fonte analítica histórica comercial/ANFIR autorizada, com território, frota, cliente, implementadora, equipamento, linha, modelo e demais campos disponíveis. Use esta fonte para frequência histórica, rankings por ocorrência, tendências e análises ao longo do histórico.",
    "historico_comercial": "Histórico comercial homologado 2023–2026 do funil Viena, com BACKLOG, OPORTUNIDADE e INTERMEDIAÇÃO-OEM. Contém cliente, equipamento, quantidade, valores nominais, observações, status reconstruído, motivo de perda, canal, implementadora, representante histórico e responsabilidade atual. É somente leitura, preserva proveniência e não representa Pipeline ativo.",
    "clientes": "Clientes do CRM dentro do escopo autorizado do usuário.",
    "oportunidades": "Oportunidades comerciais do CRM dentro do escopo autorizado.",
    "itens_oportunidade": "Itens/equipamentos vinculados às oportunidades autorizadas.",
    "propostas": "Propostas comerciais autorizadas.",
    "aceites": "Aceites/recusas de propostas autorizadas.",
    "pedidos": "Pedidos comerciais autorizados e seu ciclo operacional.",
    "atividades": "Atividades, visitas e acompanhamentos autorizados.",
    "vendas": "Vendas autorizadas e seus vínculos registrados.",
    "implementadoras_cadastro": "Cadastro canônico atual de implementadoras do CTI. Use para existência, identidade, status e listagem cadastral atual; não usar como substituto do histórico ANFIR para ranking por frequência ou atuação histórica.",
    "catalogo_produtos": "Catálogo oficial de linhas, modelos e aliases de equipamentos do CTI.",
    "perfil_usuario": "Perfil operacional do usuário atual, sem credenciais ou segredos.",
}


def _normalizar(valor: Any) -> str:
    return str(valor or "").strip().casefold()


def _sanitizar_registro(registro: dict[str, Any]) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    for chave, valor in registro.items():
        chave_norm = _normalizar(chave)
        if chave_norm in CAMPOS_SENSIVEIS or any(t in chave_norm for t in ("password", "senha", "secret", "token", "api_key")):
            continue
        resultado[str(chave)] = valor
    return resultado


def _fonte_catalogo_produtos() -> list[dict[str, Any]]:
    catalogo = listar_catalogo()
    linhas = catalogo.get("lines", []) if isinstance(catalogo, dict) else []
    saida: list[dict[str, Any]] = []
    for linha in linhas if isinstance(linhas, list) else []:
        if not isinstance(linha, dict):
            continue
        base_linha = {chave: valor for chave, valor in linha.items() if chave != "models"}
        modelos = linha.get("models") or []
        if not isinstance(modelos, list) or not modelos:
            saida.append(base_linha)
            continue
        for modelo in modelos:
            item = dict(base_linha)
            if isinstance(modelo, dict):
                item.update({f"modelo_{chave}": valor for chave, valor in modelo.items()})
            else:
                item["modelo_nome"] = modelo
            saida.append(item)
    return saida


def _fonte_perfil_usuario(usuario_id: str) -> list[dict[str, Any]]:
    tabelas = ("cti_users", "usuarios")
    for tabela in tabelas:
        registros = _consulta_segura(tabela)
        encontrados = [
            _sanitizar_registro(item)
            for item in registros
            if str(item.get("id") or item.get("usuario_id") or "") == str(usuario_id)
        ]
        if encontrados:
            return encontrados
    return []


def _fonte_historico_comercial(tipo_usuario: str) -> list[dict[str, Any]]:
    # A fonte foi homologada pelo ADMIN_MASTER. Até existir regra territorial
    # determinística para todos os perfis, não ampliar acesso de terceiros.
    if str(tipo_usuario or "").upper() != "ADMIN_MASTER":
        return []
    return [_sanitizar_registro(dict(item)) for item in carregar_historico_comercial()]


def _carregar_fontes(usuario_id: str, tipo_usuario: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    crm = _escopo_autorizado(usuario_id, tipo_usuario)
    historico = repository.buscar_cti_anfir()
    historico, escopo_territorial, erro_rbac = _aplicar_rbac(historico, usuario_id, tipo_usuario, None)
    if erro_rbac:
        historico = []

    historico_comercial = _fonte_historico_comercial(tipo_usuario)
    implementadoras = [
        _sanitizar_registro(item)
        for item in _consulta_segura("cti_implementadoras")
        if item.get("ativo") is not False
    ]

    fontes = {
        "historico_anfir": [_sanitizar_registro(item) for item in historico],
        "historico_comercial": historico_comercial,
        "clientes": [_sanitizar_registro(item) for item in crm.get("clientes", [])],
        "oportunidades": [_sanitizar_registro(item) for item in crm.get("oportunidades", [])],
        "itens_oportunidade": [_sanitizar_registro(item) for item in crm.get("itens", [])],
        "propostas": [_sanitizar_registro(item) for item in crm.get("propostas", [])],
        "aceites": [_sanitizar_registro(item) for item in crm.get("aceites", [])],
        "pedidos": [_sanitizar_registro(item) for item in crm.get("pedidos", [])],
        "atividades": [_sanitizar_registro(item) for item in crm.get("atividades", [])],
        "vendas": [_sanitizar_registro(item) for item in crm.get("vendas", [])],
        "implementadoras_cadastro": implementadoras,
        "catalogo_produtos": _fonte_catalogo_produtos(),
        "perfil_usuario": _fonte_perfil_usuario(usuario_id),
    }
    metadados = {
        "escopo_territorial": escopo_territorial,
        "erro_rbac_historico": erro_rbac,
        "historico_comercial": {
            "autorizado": str(tipo_usuario or "").upper() == "ADMIN_MASTER",
            "total_registros": len(historico_comercial),
            "modo": "somente_leitura",
            "nao_promove_crm": True,
        },
    }
    return fontes, metadados


def _campos(registros: list[dict[str, Any]]) -> list[str]:
    campos: set[str] = set()
    for item in registros[:200]:
        campos.update(str(chave) for chave in item.keys())
    return sorted(campos)


def _validar_plano_campos(
    registros: list[dict[str, Any]],
    *,
    filtros: list[dict[str, Any]],
    agrupar_por: list[str],
    metricas: list[dict[str, Any]],
    ordenar_por: str | None,
) -> dict[str, Any] | None:
    campos_disponiveis = _campos(registros)
    disponiveis = set(campos_disponiveis)
    invalidos: set[str] = set()

    for filtro in filtros:
        if not isinstance(filtro, dict):
            continue
        campo = str(filtro.get("campo") or "").strip()
        if campo and campo not in disponiveis:
            invalidos.add(campo)

    for campo in agrupar_por:
        campo = str(campo or "").strip()
        if campo and campo not in disponiveis:
            invalidos.add(campo)

    aliases_metricas: set[str] = set()
    for metrica in metricas:
        if not isinstance(metrica, dict):
            continue
        campo = str(metrica.get("campo") or "").strip()
        alias = str(metrica.get("alias") or "").strip()
        if alias:
            aliases_metricas.add(alias)
        if campo and campo not in disponiveis:
            invalidos.add(campo)

    campo_ordenacao = str(ordenar_por or "").strip()
    if campo_ordenacao and campo_ordenacao not in disponiveis and campo_ordenacao not in aliases_metricas and campo_ordenacao not in set(agrupar_por):
        invalidos.add(campo_ordenacao)

    if not invalidos:
        return None
    return {
        "erro": "Plano de consulta contém campo(s) inexistente(s) na fonte selecionada. Consulte o catálogo e refaça o plano com campos disponíveis.",
        "campos_invalidos": sorted(invalidos),
        "campos_disponiveis": campos_disponiveis,
    }


def catalogar_universo_cti(usuario_id: str, tipo_usuario: str) -> dict[str, Any]:
    fontes, metadados = _carregar_fontes(usuario_id, tipo_usuario)
    catalogo = []
    for nome, descricao in FONTES_PUBLICAS.items():
        registros = fontes.get(nome, [])
        campos = _campos(registros)
        relacoes_candidatas = [campo for campo in campos if campo.endswith("_id")]
        catalogo.append({
            "fonte": nome,
            "descricao": descricao,
            "total_registros_autorizados": len(registros),
            "campos_disponiveis": campos,
            "campos_relacionais_candidatos": relacoes_candidatas,
        })
    return {
        "modo": "somente_leitura",
        "fontes": catalogo,
        "escopo": metadados,
        "regra": "Descubra os dados pelo catálogo, respeite a função analítica descrita de cada fonte e consulte por plano estruturado; não existe SQL livre nem escrita nesta camada.",
    }


def _comparar(valor: Any, operador: str, esperado: Any) -> bool:
    op = str(operador or "eq").lower()
    if op == "is_null":
        return valor in (None, "")
    if op == "not_null":
        return valor not in (None, "")
    if op == "contains":
        return _normalizar(esperado) in _normalizar(valor)
    if op == "in":
        candidatos = esperado if isinstance(esperado, list) else [esperado]
        return _normalizar(valor) in {_normalizar(item) for item in candidatos}
    if op in {"gt", "gte", "lt", "lte"}:
        try:
            a = float(valor)
            b = float(esperado)
        except (TypeError, ValueError):
            a = str(valor or "")
            b = str(esperado or "")
        return {"gt": a > b, "gte": a >= b, "lt": a < b, "lte": a <= b}[op]
    if op == "neq":
        return _normalizar(valor) != _normalizar(esperado)
    return _normalizar(valor) == _normalizar(esperado)


def _aplicar_filtros(registros: list[dict[str, Any]], filtros: list[dict[str, Any]], termo: str | None) -> list[dict[str, Any]]:
    saida = registros
    for filtro in filtros:
        if not isinstance(filtro, dict):
            continue
        campo = str(filtro.get("campo") or "").strip()
        if not campo:
            continue
        operador = str(filtro.get("operador") or "eq")
        esperado = filtro.get("valor")
        saida = [item for item in saida if _comparar(item.get(campo), operador, esperado)]
    if termo:
        alvo = _normalizar(termo)
        saida = [
            item for item in saida
            if alvo in _normalizar(json.dumps(item, ensure_ascii=False, default=str))
        ]
    return saida


def _numero(valor: Any) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _agregar(registros: list[dict[str, Any]], agrupar_por: list[str], metricas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grupos: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in registros:
        chave = tuple(item.get(campo) for campo in agrupar_por)
        grupos[chave].append(item)

    resultado: list[dict[str, Any]] = []
    for chave, itens in grupos.items():
        linha = {campo: chave[indice] for indice, campo in enumerate(agrupar_por)}
        for metrica in metricas:
            if not isinstance(metrica, dict):
                continue
            operacao = str(metrica.get("operacao") or "count").lower()
            campo = str(metrica.get("campo") or "").strip()
            alias = str(metrica.get("alias") or f"{operacao}_{campo or 'registros'}")
            if operacao == "count":
                linha[alias] = len(itens) if not campo else sum(1 for item in itens if item.get(campo) not in (None, ""))
                continue
            valores = [_numero(item.get(campo)) for item in itens]
            numeros = [valor for valor in valores if valor is not None]
            if operacao == "sum":
                linha[alias] = round(sum(numeros), 4)
            elif operacao == "avg":
                linha[alias] = round(sum(numeros) / len(numeros), 4) if numeros else None
            elif operacao == "min":
                linha[alias] = min(numeros) if numeros else None
            elif operacao == "max":
                linha[alias] = max(numeros) if numeros else None
        resultado.append(linha)
    return resultado


def _ordenar(registros: list[dict[str, Any]], ordenar_por: str | None, direcao: str) -> list[dict[str, Any]]:
    if not ordenar_por:
        return registros

    def chave(item: dict[str, Any]):
        valor = item.get(ordenar_por)
        numero = _numero(valor)
        if numero is not None:
            return (0, numero)
        return (1, _normalizar(valor))

    return sorted(registros, key=chave, reverse=str(direcao or "desc").lower() == "desc")


def consultar_universo_cti(
    usuario_id: str,
    tipo_usuario: str,
    *,
    fonte: str,
    filtros: list[dict[str, Any]] | None = None,
    termo: str | None = None,
    agrupar_por: list[str] | None = None,
    metricas: list[dict[str, Any]] | None = None,
    ordenar_por: str | None = None,
    direcao: str = "desc",
    limite: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    fontes, metadados = _carregar_fontes(usuario_id, tipo_usuario)
    nome = str(fonte or "").strip()
    if nome not in fontes:
        return {
            "erro": "Fonte inexistente ou não autorizada.",
            "fontes_disponiveis": sorted(fontes),
        }

    registros = fontes[nome]
    filtros_seguros = [item for item in (filtros or []) if isinstance(item, dict)]
    agrupamentos = [str(item) for item in (agrupar_por or []) if str(item).strip()][:3]
    metricas_seguras = [item for item in (metricas or []) if isinstance(item, dict)][:8]

    erro_plano = _validar_plano_campos(
        registros,
        filtros=filtros_seguros,
        agrupar_por=agrupamentos,
        metricas=metricas_seguras,
        ordenar_por=ordenar_por,
    )
    if erro_plano:
        return {
            "fonte": nome,
            "descricao": FONTES_PUBLICAS[nome],
            "modo": "somente_leitura",
            "escopo": metadados,
            **erro_plano,
        }

    filtrados = _aplicar_filtros(registros, filtros_seguros, termo)
    total_filtrado = len(filtrados)

    if agrupamentos:
        if not metricas_seguras:
            metricas_seguras = [{"operacao": "count", "campo": None, "alias": "quantidade_registros"}]
        saida = _agregar(filtrados, agrupamentos, metricas_seguras)
    else:
        saida = filtrados

    saida = _ordenar(saida, ordenar_por, direcao)
    limite = max(1, min(int(limite or 50), 200))
    offset = max(0, int(offset or 0))
    pagina = saida[offset:offset + limite]

    return {
        "fonte": nome,
        "descricao": FONTES_PUBLICAS[nome],
        "modo": "somente_leitura",
        "escopo": metadados,
        "total_fonte_autorizado": len(registros),
        "total_filtrado": total_filtrado,
        "total_resultado": len(saida),
        "offset": offset,
        "limite": limite,
        "tem_mais": offset + limite < len(saida),
        "campos_disponiveis": _campos(registros),
        "plano_executado": {
            "filtros": filtros_seguros,
            "termo": termo,
            "agrupar_por": agrupamentos,
            "metricas": metricas_seguras,
            "ordenar_por": ordenar_por,
            "direcao": direcao,
        },
        "resultado": pagina,
    }