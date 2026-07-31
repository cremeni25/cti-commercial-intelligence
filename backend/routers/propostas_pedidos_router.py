from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-documentos", tags=["CRM Documentos Comerciais"])


class ItemOportunidadeCreate(BaseModel):
    linha_produto: str
    equipamento: str
    configuracao: str | None = None
    quantidade: int = Field(default=1, gt=0)
    preco_unitario: float = Field(default=0, ge=0)
    desconto_percentual: float = Field(default=0, ge=0, le=100)
    condicao_pagamento: str | None = None
    prazo_entrega: str | None = None
    validade_condicao: str | None = None
    frete: str | None = None
    local_entrega: str | None = None
    garantia: str | None = None
    opcionais: list[str] = Field(default_factory=list)
    observacoes_comerciais: str | None = None
    observacoes_tecnicas: str | None = None
    ordem: int = 0


class ItemOportunidadeUpdate(BaseModel):
    linha_produto: str | None = None
    equipamento: str | None = None
    configuracao: str | None = None
    quantidade: int | None = Field(default=None, gt=0)
    preco_unitario: float | None = Field(default=None, ge=0)
    desconto_percentual: float | None = Field(default=None, ge=0, le=100)
    condicao_pagamento: str | None = None
    prazo_entrega: str | None = None
    validade_condicao: str | None = None
    frete: str | None = None
    local_entrega: str | None = None
    garantia: str | None = None
    opcionais: list[str] | None = None
    observacoes_comerciais: str | None = None
    observacoes_tecnicas: str | None = None
    status: str | None = None
    ordem: int | None = None


class GerarPropostaRequest(BaseModel):
    responsavel_id: str
    validade: str | None = None
    observacoes: str | None = None
    condicoes_adicionais: str | None = None


class SolicitarAceiteRequest(BaseModel):
    metodo: Literal["PRESENCIAL_TELA", "REMOTO_LINK"]
    nome_signatario: str
    documento_signatario: str | None = None
    email_signatario: str | None = None
    telefone_signatario: str | None = None


class ConfirmarAceiteRequest(BaseModel):
    aceite_termos: bool
    assinatura_desenhada: str | None = None
    codigo_validacao: str | None = None
    ip_origem: str | None = None
    user_agent: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    evidencias: dict[str, Any] = Field(default_factory=dict)


class ConverterPedidoRequest(BaseModel):
    numero: str | None = None
    responsavel_id: str | None = None
    data_pedido: str | None = None
    origem_comercial: str = "CRM"


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail=detalhe)
    return dados[0]


def _numero_proposta() -> str:
    agora = datetime.now(timezone.utc)
    return f"PROP-{agora:%Y%m%d}-{uuid4().hex[:8].upper()}"


def _numero_pedido() -> str:
    agora = datetime.now(timezone.utc)
    return f"PED-{agora:%Y%m%d}-{uuid4().hex[:8].upper()}"


def _valor_item(item: dict[str, Any]) -> float:
    quantidade = float(item.get("quantidade") or 0)
    preco = float(item.get("preco_unitario") or 0)
    desconto = float(item.get("desconto_percentual") or 0)
    return round(quantidade * preco * (1 - desconto / 100), 2)


def _snapshot(oportunidade: dict[str, Any], item: dict[str, Any], modelo: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "oportunidade": oportunidade,
        "item": {**item, "valor_total_calculado": _valor_item(item)},
        "modelo": modelo,
        "gerado_em": _agora(),
    }


def _modelo_ativo(item: dict[str, Any]) -> dict[str, Any] | None:
    modelos = (
        supabase.table("cti_modelos_proposta")
        .select("*")
        .eq("linha_produto", item["linha_produto"])
        .eq("equipamento", item["equipamento"])
        .eq("ativo", True)
        .order("versao", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return modelos[0] if modelos else None


def _atualizar_status_oportunidade(oportunidade_id: str) -> None:
    itens = supabase.table("cti_oportunidade_itens").select("status").eq("oportunidade_id", oportunidade_id).execute().data or []
    statuses = {str(item.get("status") or "EM_NEGOCIACAO") for item in itens}
    if statuses and statuses <= {"CONVERTIDO_PEDIDO"}:
        status = "GANHO"
    elif "CONVERTIDO_PEDIDO" in statuses:
        status = "PARCIALMENTE_GANHO"
    elif "PROPOSTA_EMITIDA" in statuses or "ACEITO" in statuses:
        status = "PROPOSTA"
    else:
        return
    supabase.table("cti_oportunidades").update({"status": status, "updated_at": _agora()}).eq("id", oportunidade_id).execute()


@router.get("/oportunidades/{oportunidade_id}/itens")
def listar_itens(oportunidade_id: str):
    _primeiro("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada")
    return (
        supabase.table("cti_oportunidade_itens")
        .select("*")
        .eq("oportunidade_id", oportunidade_id)
        .order("ordem")
        .order("created_at")
        .execute()
        .data
        or []
    )


@router.post("/oportunidades/{oportunidade_id}/itens")
def criar_item(oportunidade_id: str, dados: ItemOportunidadeCreate):
    _primeiro("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada")
    payload = dados.model_dump()
    payload["oportunidade_id"] = oportunidade_id
    payload["linha_produto"] = payload["linha_produto"].strip().upper()
    payload["equipamento"] = payload["equipamento"].strip().upper()
    return supabase.table("cti_oportunidade_itens").insert(payload).execute().data


@router.put("/itens/{item_id}")
def atualizar_item(item_id: str, dados: ItemOportunidadeUpdate):
    item = _primeiro("cti_oportunidade_itens", item_id, "Item da oportunidade não encontrado")
    payload = dados.model_dump(exclude_none=True)
    if "linha_produto" in payload:
        payload["linha_produto"] = payload["linha_produto"].strip().upper()
    if "equipamento" in payload:
        payload["equipamento"] = payload["equipamento"].strip().upper()
    payload["updated_at"] = _agora()
    atualizado = supabase.table("cti_oportunidade_itens").update(payload).eq("id", item_id).execute().data
    _atualizar_status_oportunidade(str(item["oportunidade_id"]))
    return atualizado


@router.delete("/itens/{item_id}")
def excluir_item(item_id: str):
    item = _primeiro("cti_oportunidade_itens", item_id, "Item da oportunidade não encontrado")
    propostas = supabase.table("cti_propostas").select("id").eq("item_oportunidade_id", item_id).limit(1).execute().data or []
    if propostas:
        raise HTTPException(status_code=409, detail="Item com proposta vinculada não pode ser excluído; utilize cancelamento.")
    supabase.table("cti_oportunidade_itens").delete().eq("id", item_id).execute()
    return {"success": True, "oportunidade_id": item["oportunidade_id"]}


@router.post("/itens/{item_id}/propostas")
def gerar_proposta(item_id: str, dados: GerarPropostaRequest):
    item = _primeiro("cti_oportunidade_itens", item_id, "Item da oportunidade não encontrado")
    oportunidade = _primeiro("cti_oportunidades", str(item["oportunidade_id"]), "Oportunidade não encontrada")
    modelo = _modelo_ativo(item)
    anteriores = supabase.table("cti_propostas").select("versao").eq("item_oportunidade_id", item_id).order("versao", desc=True).limit(1).execute().data or []
    versao = int(anteriores[0]["versao"]) + 1 if anteriores else 1
    snapshot = _snapshot(oportunidade, item, modelo)
    snapshot["condicoes_adicionais"] = dados.condicoes_adicionais or item.get("condicao_pagamento")
    snapshot["produto"] = item.get("linha_produto")
    snapshot["equipamento"] = item.get("equipamento")
    snapshot["validade"] = dados.validade or item.get("validade_condicao")
    snapshot["observacoes"] = dados.observacoes
    snapshot["responsavel_id"] = dados.responsavel_id
    hash_documento = sha256(repr(snapshot).encode("utf-8")).hexdigest()
    payload = {
        "numero": _numero_proposta(),
        "cliente_id": oportunidade.get("cliente_id"),
        "oportunidade_id": oportunidade["id"],
        "item_oportunidade_id": item_id,
        "modelo_proposta_id": modelo.get("id") if modelo else None,
        "valor": _valor_item(item),
        "status": "ELABORACAO",
        "status_documento": "RASCUNHO",
        "versao": versao,
        "snapshot_dados": snapshot,
        "hash_documento": hash_documento,
    }
    proposta = supabase.table("cti_propostas").insert(payload).execute().data or []
    supabase.table("cti_oportunidade_itens").update({"status": "PROPOSTA_EMITIDA", "updated_at": _agora()}).eq("id", item_id).execute()
    _atualizar_status_oportunidade(str(oportunidade["id"]))
    return proposta


@router.get("/itens/{item_id}/propostas")
def listar_propostas_item(item_id: str):
    _primeiro("cti_oportunidade_itens", item_id, "Item da oportunidade não encontrado")
    return supabase.table("cti_propostas").select("*").eq("item_oportunidade_id", item_id).order("versao", desc=True).execute().data or []


@router.post("/propostas/{proposta_id}/emitir")
def emitir_proposta(proposta_id: str):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada")
    if proposta.get("status_documento") not in {"RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"}:
        raise HTTPException(status_code=409, detail="A proposta não está em condição de emissão.")
    return supabase.table("cti_propostas").update({"status_documento": "EMITIDA", "status": "ENVIADA", "emitida_em": _agora(), "updated_at": _agora()}).eq("id", proposta_id).execute().data


@router.post("/propostas/{proposta_id}/aceites")
def solicitar_aceite(proposta_id: str, dados: SolicitarAceiteRequest):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada")
    if proposta.get("status_documento") not in {"EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"}:
        raise HTTPException(status_code=409, detail="Emita a proposta antes de solicitar o aceite.")
    payload = {"proposta_id": proposta_id, **dados.model_dump(), "status": "PENDENTE"}
    aceite = supabase.table("cti_proposta_aceites").insert(payload).execute().data or []
    return {"aceite": aceite[0] if aceite else None, "link_token": str(aceite[0]["id"]) if aceite and dados.metodo == "REMOTO_LINK" else None}


@router.post("/aceites/{aceite_id}/confirmar")
def confirmar_aceite(aceite_id: str, dados: ConfirmarAceiteRequest):
    aceite = _primeiro("cti_proposta_aceites", aceite_id, "Solicitação de aceite não encontrada")
    if not dados.aceite_termos:
        raise HTTPException(status_code=422, detail="O aceite expresso dos termos é obrigatório.")
    if aceite.get("status") not in {"PENDENTE", "VISUALIZADO"}:
        raise HTTPException(status_code=409, detail="Este aceite já foi finalizado.")
    codigo_hash = sha256(dados.codigo_validacao.encode("utf-8")).hexdigest() if dados.codigo_validacao else None
    payload = {
        "aceite_termos": True,
        "assinatura_desenhada": dados.assinatura_desenhada,
        "codigo_validacao_hash": codigo_hash,
        "ip_origem": dados.ip_origem,
        "user_agent": dados.user_agent,
        "latitude": dados.latitude,
        "longitude": dados.longitude,
        "evidencias": dados.evidencias,
        "status": "ACEITO",
        "aceito_em": _agora(),
    }
    atualizado = supabase.table("cti_proposta_aceites").update(payload).eq("id", aceite_id).execute().data or []
    proposta = _primeiro("cti_propostas", str(aceite["proposta_id"]), "Proposta não encontrada")
    supabase.table("cti_propostas").update({"status_documento": "ACEITA", "status": "APROVADA", "aceita_em": _agora(), "updated_at": _agora()}).eq("id", proposta["id"]).execute()
    if proposta.get("item_oportunidade_id"):
        supabase.table("cti_oportunidade_itens").update({"status": "ACEITO", "updated_at": _agora()}).eq("id", proposta["item_oportunidade_id"]).execute()
    return atualizado


@router.post("/propostas/{proposta_id}/converter-pedido")
def converter_em_pedido(proposta_id: str, dados: ConverterPedidoRequest):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada")
    if proposta.get("status_documento") != "ACEITA":
        raise HTTPException(status_code=409, detail="Somente proposta aceita pode ser convertida em pedido.")
    aceites = supabase.table("cti_proposta_aceites").select("*").eq("proposta_id", proposta_id).eq("status", "ACEITO").order("aceito_em", desc=True).limit(1).execute().data or []
    if not aceites:
        raise HTTPException(status_code=409, detail="A proposta não possui aceite válido registrado.")
    existente = supabase.table("cti_pedidos").select("*").eq("proposta_aceita_id", proposta_id).limit(1).execute().data or []
    if existente:
        return existente
    payload = {
        "numero": dados.numero or _numero_pedido(),
        "cliente_id": proposta.get("cliente_id"),
        "proposta_id": proposta_id,
        "proposta_aceita_id": proposta_id,
        "oportunidade_id": proposta.get("oportunidade_id"),
        "item_oportunidade_id": proposta.get("item_oportunidade_id"),
        "aceite_id": aceites[0]["id"],
        "responsavel_id": dados.responsavel_id or (proposta.get("snapshot_dados") or {}).get("responsavel_id"),
        "valor": proposta.get("valor") or 0,
        "status": "ABERTO",
        "data_pedido": dados.data_pedido or datetime.now(timezone.utc).date().isoformat(),
        "origem_comercial": dados.origem_comercial,
        "dossie_documentos": [
            {"tipo": "PROPOSTA", "id": proposta_id, "hash": proposta.get("hash_documento")},
            {"tipo": "ACEITE", "id": aceites[0]["id"]},
        ],
    }
    pedido = supabase.table("cti_pedidos").insert(payload).execute().data or []
    supabase.table("cti_propostas").update({"status_documento": "CONVERTIDA_PEDIDO", "updated_at": _agora()}).eq("id", proposta_id).execute()
    if proposta.get("item_oportunidade_id"):
        supabase.table("cti_oportunidade_itens").update({"status": "CONVERTIDO_PEDIDO", "updated_at": _agora()}).eq("id", proposta["item_oportunidade_id"]).execute()
    if proposta.get("oportunidade_id"):
        _atualizar_status_oportunidade(str(proposta["oportunidade_id"]))
    return pedido


@router.get("/funil-carrier")
def funil_carrier():
    oportunidades = supabase.table("cti_oportunidades").select("*").eq("origem", "CRM_APP").execute().data or []
    ids = {item["id"] for item in oportunidades if item.get("id")}
    itens = supabase.table("cti_oportunidade_itens").select("*").execute().data or []
    propostas = supabase.table("cti_propostas").select("*").execute().data or []
    pedidos = supabase.table("cti_pedidos").select("*").execute().data or []
    por_oportunidade = {item["id"]: item for item in oportunidades if item.get("id")}
    propostas_item: dict[str, list[dict[str, Any]]] = {}
    pedidos_item: dict[str, list[dict[str, Any]]] = {}
    for proposta in propostas:
        chave = str(proposta.get("item_oportunidade_id") or "")
        propostas_item.setdefault(chave, []).append(proposta)
    for pedido in pedidos:
        chave = str(pedido.get("item_oportunidade_id") or "")
        pedidos_item.setdefault(chave, []).append(pedido)
    return [
        {
            "oportunidade_id": item.get("oportunidade_id"),
            "cliente_id": por_oportunidade.get(item.get("oportunidade_id"), {}).get("cliente_id"),
            "responsavel_id": por_oportunidade.get(item.get("oportunidade_id"), {}).get("responsavel_id"),
            "linha_produto": item.get("linha_produto"),
            "equipamento": item.get("equipamento"),
            "quantidade": item.get("quantidade"),
            "valor_total": item.get("valor_total") or _valor_item(item),
            "status_item": item.get("status"),
            "propostas": len(propostas_item.get(str(item.get("id")), [])),
            "proposta_aceita": any(p.get("status_documento") in {"ACEITA", "CONVERTIDA_PEDIDO"} for p in propostas_item.get(str(item.get("id")), [])),
            "pedido_gerado": bool(pedidos_item.get(str(item.get("id")))),
            "previsao_fechamento": por_oportunidade.get(item.get("oportunidade_id"), {}).get("data_fechamento_prevista"),
            "probabilidade": por_oportunidade.get(item.get("oportunidade_id"), {}).get("probabilidade"),
        }
        for item in itens
        if item.get("oportunidade_id") in ids
    ]
