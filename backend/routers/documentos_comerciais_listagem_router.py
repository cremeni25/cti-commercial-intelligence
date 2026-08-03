from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-documentos", tags=["CRM Documentos Comerciais"])


def _mapa_clientes(ids: set[str]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    registros = supabase.table("cti_clientes").select("*").in_("id", list(ids)).execute().data or []
    return {str(item.get("id")): item for item in registros if item.get("id")}


def _mapa_itens(ids: set[str]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    registros = supabase.table("cti_oportunidade_itens").select("*").in_("id", list(ids)).execute().data or []
    return {str(item.get("id")): item for item in registros if item.get("id")}


@router.get("/propostas")
def listar_propostas_operacionais():
    propostas = (
        supabase.table("cti_propostas")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    clientes = _mapa_clientes({str(item.get("cliente_id")) for item in propostas if item.get("cliente_id")})
    itens = _mapa_itens({str(item.get("item_oportunidade_id")) for item in propostas if item.get("item_oportunidade_id")})
    return [
        {
            **proposta,
            "cliente_nome": (clientes.get(str(proposta.get("cliente_id"))) or {}).get("razao_social")
            or (clientes.get(str(proposta.get("cliente_id"))) or {}).get("nome"),
            "equipamento": (itens.get(str(proposta.get("item_oportunidade_id"))) or {}).get("equipamento"),
            "quantidade": (itens.get(str(proposta.get("item_oportunidade_id"))) or {}).get("quantidade"),
        }
        for proposta in propostas
    ]


@router.get("/pedidos")
def listar_pedidos_operacionais():
    pedidos = (
        supabase.table("cti_pedidos")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    clientes = _mapa_clientes({str(item.get("cliente_id")) for item in pedidos if item.get("cliente_id")})
    itens = _mapa_itens({str(item.get("item_oportunidade_id")) for item in pedidos if item.get("item_oportunidade_id")})
    return [
        {
            **pedido,
            "cliente_nome": (clientes.get(str(pedido.get("cliente_id"))) or {}).get("razao_social")
            or (clientes.get(str(pedido.get("cliente_id"))) or {}).get("nome"),
            "equipamento": (itens.get(str(pedido.get("item_oportunidade_id"))) or {}).get("equipamento"),
            "quantidade": (itens.get(str(pedido.get("item_oportunidade_id"))) or {}).get("quantidade"),
        }
        for pedido in pedidos
    ]
