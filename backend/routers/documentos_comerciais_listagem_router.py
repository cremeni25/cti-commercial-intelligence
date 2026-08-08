from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-documentos", tags=["CRM Documentos Comerciais"])


def _mapa_clientes(ids: set[str]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    resultado: dict[str, dict[str, Any]] = {}
    for tabela in ("cti_clientes", "clientes"):
        try:
            registros = supabase.table(tabela).select("*").in_("id", list(ids)).execute().data or []
        except Exception:
            registros = []
        for item in registros:
            identificador = str(item.get("id") or "")
            if identificador and identificador not in resultado:
                resultado[identificador] = item
    return resultado


def _mapa_itens(ids: set[str]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    registros = supabase.table("cti_oportunidade_itens").select("*").in_("id", list(ids)).execute().data or []
    return {str(item.get("id")): item for item in registros if item.get("id")}


def _nome_cliente(item: dict[str, Any] | None) -> str | None:
    if not item:
        return None
    return item.get("razao_social") or item.get("nome_fantasia") or item.get("nome") or item.get("empresa")


@router.get("/propostas")
def listar_propostas_operacionais():
    propostas = supabase.table("cti_propostas").select("*").order("created_at", desc=True).execute().data or []
    clientes = _mapa_clientes({str(item.get("cliente_id")) for item in propostas if item.get("cliente_id")})
    itens = _mapa_itens({str(item.get("item_oportunidade_id")) for item in propostas if item.get("item_oportunidade_id")})
    return [{**proposta,"cliente_nome":_nome_cliente(clientes.get(str(proposta.get("cliente_id")))),"equipamento":(itens.get(str(proposta.get("item_oportunidade_id"))) or {}).get("equipamento"),"quantidade":(itens.get(str(proposta.get("item_oportunidade_id"))) or {}).get("quantidade")} for proposta in propostas]


@router.get("/pedidos")
def listar_pedidos_operacionais():
    pedidos = supabase.table("cti_pedidos").select("*").order("created_at", desc=True).execute().data or []
    clientes = _mapa_clientes({str(item.get("cliente_id")) for item in pedidos if item.get("cliente_id")})
    itens = _mapa_itens({str(item.get("item_oportunidade_id")) for item in pedidos if item.get("item_oportunidade_id")})
    return [{**pedido,"cliente_nome":_nome_cliente(clientes.get(str(pedido.get("cliente_id")))),"equipamento":(itens.get(str(pedido.get("item_oportunidade_id"))) or {}).get("equipamento"),"quantidade":(itens.get(str(pedido.get("item_oportunidade_id"))) or {}).get("quantidade")} for pedido in pedidos]
