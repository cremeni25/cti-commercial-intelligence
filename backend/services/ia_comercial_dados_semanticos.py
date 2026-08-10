from __future__ import annotations

import json
from typing import Any

from services.ia_comercial_cti import _consulta_segura

DOMINIOS_TABELAS = {
    "clientes": ("clientes", "cti_clientes"),
    "oportunidades": ("cti_oportunidades",),
    "itens": ("cti_oportunidade_itens",),
    "propostas": ("cti_propostas",),
    "pedidos": ("cti_pedidos",),
    "atividades": ("cti_atividades",),
    "vendas": ("vendas",),
}


def _normalizar(valor: Any) -> str:
    return str(valor or "").strip().casefold()


def _carregar_dominio(dominio: str) -> list[dict[str, Any]]:
    tabelas = DOMINIOS_TABELAS.get(dominio)
    if not tabelas:
        return []
    for tabela in tabelas:
        registros = _consulta_segura(tabela)
        if registros:
            return registros
    return []


def _escopo_autorizado(usuario_id: str, tipo_usuario: str) -> dict[str, list[dict[str, Any]]]:
    oportunidades = _carregar_dominio("oportunidades")
    clientes = _carregar_dominio("clientes")
    propostas = _carregar_dominio("propostas")
    pedidos = _carregar_dominio("pedidos")
    atividades = _carregar_dominio("atividades")
    itens = _carregar_dominio("itens")
    vendas = _carregar_dominio("vendas")

    if tipo_usuario == "ADMIN_MASTER":
        return {
            "clientes": clientes,
            "oportunidades": oportunidades,
            "itens": itens,
            "propostas": propostas,
            "pedidos": pedidos,
            "atividades": atividades,
            "vendas": vendas,
        }

    oportunidades = [
        item
        for item in oportunidades
        if str(item.get("responsavel_id") or "") == usuario_id
    ]
    oportunidade_ids = {str(item.get("id")) for item in oportunidades if item.get("id")}
    cliente_ids = {str(item.get("cliente_id")) for item in oportunidades if item.get("cliente_id")}

    clientes = [item for item in clientes if str(item.get("id") or "") in cliente_ids]
    propostas = [item for item in propostas if str(item.get("oportunidade_id") or "") in oportunidade_ids]
    pedidos = [item for item in pedidos if str(item.get("oportunidade_id") or "") in oportunidade_ids]
    itens = [item for item in itens if str(item.get("oportunidade_id") or "") in oportunidade_ids]
    atividades = [
        item
        for item in atividades
        if str(item.get("responsavel_id") or item.get("usuario_id") or "") == usuario_id
    ]
    vendas = [
        item
        for item in vendas
        if (
            str(item.get("oportunidade_id") or "") in oportunidade_ids
            or str(item.get("cliente_id") or "") in cliente_ids
        )
    ]

    return {
        "clientes": clientes,
        "oportunidades": oportunidades,
        "itens": itens,
        "propostas": propostas,
        "pedidos": pedidos,
        "atividades": atividades,
        "vendas": vendas,
    }


def consultar_dominio_semantico(
    dominio: str,
    usuario_id: str,
    tipo_usuario: str,
    *,
    termo: str | None = None,
    status: str | None = None,
    limite: int = 30,
    offset: int = 0,
) -> dict[str, Any]:
    if dominio not in DOMINIOS_TABELAS:
        return {"erro": "Domínio CTI não autorizado.", "dominio": dominio}

    limite = max(1, min(int(limite or 30), 100))
    offset = max(0, int(offset or 0))
    registros = _escopo_autorizado(usuario_id, tipo_usuario).get(dominio, [])

    if termo:
        alvo = _normalizar(termo)
        registros = [
            item
            for item in registros
            if alvo in _normalizar(json.dumps(item, ensure_ascii=False, default=str))
        ]

    if status:
        alvo_status = _normalizar(status)
        registros = [item for item in registros if _normalizar(item.get("status")) == alvo_status]

    total = len(registros)
    pagina = registros[offset : offset + limite]

    return {
        "dominio": dominio,
        "escopo": "global" if tipo_usuario == "ADMIN_MASTER" else "usuario_autorizado",
        "total_encontrado": total,
        "offset": offset,
        "limite": limite,
        "tem_mais": offset + len(pagina) < total,
        "resultado": pagina,
    }
