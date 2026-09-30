from __future__ import annotations

import time
from typing import Any, Callable

import httpx
from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-documentos", tags=["CRM Documentos Comerciais"])

TRANSIENT_ERRORS = (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError, httpx.TimeoutException)


def _leitura_resiliente(query_factory: Callable[[], Any], tentativas: int = 3) -> list[dict[str, Any]]:
    for tentativa in range(tentativas):
        try:
            return query_factory().execute().data or []
        except TRANSIENT_ERRORS as erro:
            if tentativa + 1 >= tentativas:
                raise HTTPException(status_code=503, detail="Fonte de dados temporariamente indisponível. Tente novamente em instantes.") from erro
            time.sleep(0.12 * (tentativa + 1))
    return []


def _mapa_clientes(ids: set[str]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    resultado: dict[str, dict[str, Any]] = {}
    for tabela in ("cti_clientes", "clientes"):
        try:
            registros = _leitura_resiliente(lambda tabela=tabela: supabase.table(tabela).select("*").in_("id", list(ids)))
        except (HTTPException, Exception):
            registros = []
        for item in registros:
            identificador = str(item.get("id") or "")
            if identificador and identificador not in resultado:
                resultado[identificador] = item
    return resultado


def _mapa_itens(ids: set[str]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    registros = _leitura_resiliente(lambda: supabase.table("cti_oportunidade_itens").select("*").in_("id", list(ids)))
    return {str(item.get("id")): item for item in registros if item.get("id")}


def _mapa_por_id(tabela: str, ids: set[str]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    try:
        registros = _leitura_resiliente(lambda: supabase.table(tabela).select("*").in_("id", list(ids)))
    except Exception:
        return {}
    return {str(item.get("id")): item for item in registros if item.get("id")}


def _nome_cliente(item: dict[str, Any] | None) -> str | None:
    if not item:
        return None
    return item.get("razao_social") or item.get("nome_fantasia") or item.get("nome") or item.get("empresa")


def _proposta_convertida_em_pedido(item: dict[str, Any]) -> bool:
    status = str(item.get("status_documento") or item.get("status") or "").upper()
    normalizado = "".join(caractere for caractere in status if caractere.isalnum())
    return normalizado == "CONVERTIDAPEDIDO"


@router.get("/propostas")
def listar_propostas_operacionais():
    propostas = _leitura_resiliente(lambda: supabase.table("cti_propostas").select("*").order("created_at", desc=True))
    propostas = [proposta for proposta in propostas if not _proposta_convertida_em_pedido(proposta)]
    clientes = _mapa_clientes({str(item.get("cliente_id")) for item in propostas if item.get("cliente_id")})
    itens = _mapa_itens({str(item.get("item_oportunidade_id")) for item in propostas if item.get("item_oportunidade_id")})
    return [{**proposta, "cliente_nome": _nome_cliente(clientes.get(str(proposta.get("cliente_id")))), "equipamento": (itens.get(str(proposta.get("item_oportunidade_id"))) or {}).get("equipamento"), "quantidade": (itens.get(str(proposta.get("item_oportunidade_id"))) or {}).get("quantidade")} for proposta in propostas]


@router.get("/pedidos")
def listar_pedidos_operacionais():
    pedidos = _leitura_resiliente(lambda: supabase.table("cti_pedidos").select("*").order("created_at", desc=True))
    clientes = _mapa_clientes({str(item.get("cliente_id")) for item in pedidos if item.get("cliente_id")})
    itens = _mapa_itens({str(item.get("item_oportunidade_id")) for item in pedidos if item.get("item_oportunidade_id")})
    propostas = _mapa_por_id("cti_propostas", {str(item.get("proposta_id") or item.get("proposta_aceita_id")) for item in pedidos if item.get("proposta_id") or item.get("proposta_aceita_id")})
    oportunidade_ids = {str(item.get("oportunidade_id")) for item in pedidos if item.get("oportunidade_id")}
    oportunidade_ids.update(str(p.get("oportunidade_id")) for p in propostas.values() if p.get("oportunidade_id"))
    oportunidades = _mapa_por_id("cti_oportunidades", oportunidade_ids)
    resultado = []
    for pedido in pedidos:
        proposta = propostas.get(str(pedido.get("proposta_id") or pedido.get("proposta_aceita_id") or ""), {})
        oportunidade_id = str(pedido.get("oportunidade_id") or proposta.get("oportunidade_id") or "")
        oportunidade = oportunidades.get(oportunidade_id, {})
        responsavel_id = pedido.get("responsavel_id") or pedido.get("usuario_id") or proposta.get("responsavel_id") or proposta.get("usuario_id") or oportunidade.get("responsavel_id") or oportunidade.get("usuario_id")
        resultado.append({**pedido, "responsavel_id": responsavel_id, "cliente_nome": _nome_cliente(clientes.get(str(pedido.get("cliente_id")))), "equipamento": (itens.get(str(pedido.get("item_oportunidade_id"))) or {}).get("equipamento"), "quantidade": (itens.get(str(pedido.get("item_oportunidade_id"))) or {}).get("quantidade")})
    return resultado
