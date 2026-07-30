from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase

router = APIRouter(prefix="/carrier-operacional", tags=["Carrier Operacional"])


class PrepararEnvioRequest(BaseModel):
    enviado_por: str | None = None
    destinatario_ids: list[str] = Field(default_factory=list)
    assunto: str | None = None
    corpo: str | None = None


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mapa_clientes() -> dict[str, str]:
    dados = supabase.table("cti_clientes").select("id,nome,razao_social,nome_fantasia").execute().data or []
    return {
        str(item.get("id")): str(item.get("razao_social") or item.get("nome") or item.get("nome_fantasia") or "Cliente")
        for item in dados
        if item.get("id")
    }


@router.get("/pedidos")
def listar_pedidos_comerciais():
    pedidos = supabase.table("cti_pedidos").select("*").order("created_at", desc=True).execute().data or []
    clientes = _mapa_clientes()
    propostas = supabase.table("cti_propostas").select("id,numero,equipamentos,produtos,status_documento,hash_documento").execute().data or []
    propostas_por_id = {str(item.get("id")): item for item in propostas if item.get("id")}
    itens = supabase.table("cti_oportunidade_itens").select("*").execute().data or []
    itens_por_id = {str(item.get("id")): item for item in itens if item.get("id")}
    aceites = supabase.table("cti_proposta_aceites").select("id,nome_signatario,metodo,aceito_em,status").execute().data or []
    aceites_por_id = {str(item.get("id")): item for item in aceites if item.get("id")}

    saida: list[dict[str, Any]] = []
    for pedido in pedidos:
        proposta = propostas_por_id.get(str(pedido.get("proposta_aceita_id") or pedido.get("proposta_id") or ""), {})
        item = itens_por_id.get(str(pedido.get("item_oportunidade_id") or ""), {})
        aceite = aceites_por_id.get(str(pedido.get("aceite_id") or ""), {})
        saida.append({
            **pedido,
            "cliente_nome": clientes.get(str(pedido.get("cliente_id") or ""), "Cliente não identificado"),
            "proposta_numero": proposta.get("numero"),
            "proposta_status": proposta.get("status_documento"),
            "hash_documento": proposta.get("hash_documento"),
            "linha_produto": item.get("linha_produto") or proposta.get("produtos"),
            "equipamento": item.get("equipamento") or proposta.get("equipamentos"),
            "quantidade": item.get("quantidade"),
            "aceite": aceite,
        })
    return saida


@router.get("/pedidos/{pedido_id}")
def detalhe_pedido(pedido_id: str):
    pedidos = supabase.table("cti_pedidos").select("*").eq("id", pedido_id).limit(1).execute().data or []
    if not pedidos:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    pedido = pedidos[0]
    proposta_id = str(pedido.get("proposta_aceita_id") or pedido.get("proposta_id") or "")
    proposta = (supabase.table("cti_propostas").select("*").eq("id", proposta_id).limit(1).execute().data or [{}])[0]
    item_id = str(pedido.get("item_oportunidade_id") or "")
    item = (supabase.table("cti_oportunidade_itens").select("*").eq("id", item_id).limit(1).execute().data or [{}])[0]
    aceite_id = str(pedido.get("aceite_id") or "")
    aceite = (supabase.table("cti_proposta_aceites").select("*").eq("id", aceite_id).limit(1).execute().data or [{}])[0]
    destinatarios = supabase.table("cti_destinatarios_carrier").select("*").eq("ativo", True).execute().data or []
    envios = supabase.table("cti_envios_carrier").select("*").eq("pedido_id", pedido_id).order("created_at", desc=True).execute().data or []
    return {
        "pedido": pedido,
        "proposta": proposta,
        "item": item,
        "aceite": aceite,
        "destinatarios_disponiveis": destinatarios,
        "envios": envios,
    }


@router.post("/pedidos/{pedido_id}/preparar-envio")
def preparar_envio_carrier(pedido_id: str, dados: PrepararEnvioRequest):
    pedidos = supabase.table("cti_pedidos").select("*").eq("id", pedido_id).limit(1).execute().data or []
    if not pedidos:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    pedido = pedidos[0]
    consulta = supabase.table("cti_destinatarios_carrier").select("*").eq("ativo", True)
    if dados.destinatario_ids:
        consulta = consulta.in_("id", dados.destinatario_ids)
    destinatarios = consulta.execute().data or []
    if not destinatarios:
        raise HTTPException(status_code=422, detail="Cadastre ou selecione ao menos um destinatário Carrier ativo.")

    documentos = pedido.get("dossie_documentos") or []
    payload = {
        "pedido_id": pedido_id,
        "proposta_id": pedido.get("proposta_aceita_id") or pedido.get("proposta_id"),
        "destinatarios": [
            {"id": item.get("id"), "nome": item.get("nome"), "email": item.get("email"), "cargo": item.get("cargo")}
            for item in destinatarios
        ],
        "documentos": documentos,
        "assunto": dados.assunto or f"Pedido comercial {pedido.get('numero') or pedido_id}",
        "corpo": dados.corpo or "Encaminhamento do dossiê comercial gerado pelo CTI.",
        "status": "PENDENTE",
        "tentativas": 0,
        "enviado_por": dados.enviado_por,
    }
    envio = supabase.table("cti_envios_carrier").insert(payload).execute().data or []
    supabase.table("cti_pedidos").update({"status_envio_carrier": "PREPARANDO", "updated_at": _agora()}).eq("id", pedido_id).execute()
    return envio


@router.get("/funil")
def funil_carrier_operacional():
    oportunidades = supabase.table("cti_oportunidades").select("*").eq("origem", "CRM_APP").execute().data or []
    oportunidades_por_id = {str(item.get("id")): item for item in oportunidades if item.get("id")}
    clientes = _mapa_clientes()
    itens = supabase.table("cti_oportunidade_itens").select("*").order("created_at", desc=True).execute().data or []
    propostas = supabase.table("cti_propostas").select("*").execute().data or []
    pedidos = supabase.table("cti_pedidos").select("*").execute().data or []

    propostas_por_item: dict[str, list[dict[str, Any]]] = {}
    pedidos_por_item: dict[str, list[dict[str, Any]]] = {}
    for proposta in propostas:
        propostas_por_item.setdefault(str(proposta.get("item_oportunidade_id") or ""), []).append(proposta)
    for pedido in pedidos:
        pedidos_por_item.setdefault(str(pedido.get("item_oportunidade_id") or ""), []).append(pedido)

    linhas = []
    for item in itens:
        oportunidade = oportunidades_por_id.get(str(item.get("oportunidade_id") or ""))
        if not oportunidade:
            continue
        propostas_item = propostas_por_item.get(str(item.get("id")), [])
        pedidos_item = pedidos_por_item.get(str(item.get("id")), [])
        ultima_proposta = sorted(propostas_item, key=lambda p: int(p.get("versao") or 0), reverse=True)[0] if propostas_item else {}
        linhas.append({
            "oportunidade_id": oportunidade.get("id"),
            "cliente": clientes.get(str(oportunidade.get("cliente_id") or ""), "Cliente não identificado"),
            "responsavel_id": oportunidade.get("responsavel_id"),
            "territorio": oportunidade.get("sub_regiao") or oportunidade.get("ddd") or oportunidade.get("estado"),
            "linha_produto": item.get("linha_produto"),
            "equipamento": item.get("equipamento"),
            "quantidade": item.get("quantidade"),
            "valor_total": item.get("valor_total"),
            "probabilidade": oportunidade.get("probabilidade"),
            "estagio": oportunidade.get("status"),
            "previsao_fechamento": oportunidade.get("data_fechamento_prevista"),
            "status_item": item.get("status"),
            "proposta_numero": ultima_proposta.get("numero"),
            "proposta_status": ultima_proposta.get("status_documento"),
            "propostas_emitidas": len(propostas_item),
            "pedido_gerado": bool(pedidos_item),
            "pedido_numero": pedidos_item[0].get("numero") if pedidos_item else None,
            "status_envio_carrier": pedidos_item[0].get("status_envio_carrier") if pedidos_item else "NAO_APLICAVEL",
            "ultima_atualizacao": oportunidade.get("updated_at") or item.get("updated_at"),
        })
    return linhas
