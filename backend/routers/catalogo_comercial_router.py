from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase
from routers.modelos_proposta_reconciliacao_router import reconciliar_modelos_com_storage

router = APIRouter(prefix="/catalogo-comercial", tags=["Catálogo Comercial"])


class CriarItemCatalogoRequest(BaseModel):
    equipamento_codigo: str
    quantidade: int = Field(default=1, gt=0)
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


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _preco_vigente(codigo: str) -> dict[str, Any] | None:
    precos = (
        supabase.table("cti_tabela_precos")
        .select("*")
        .eq("equipamento_codigo", codigo)
        .eq("ativo", True)
        .lte("vigencia_inicio", date.today().isoformat())
        .order("vigencia_inicio", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return precos[0] if precos else None


def _equipamento(codigo: str) -> dict[str, Any]:
    dados = (
        supabase.table("cti_catalogo_equipamentos")
        .select("*")
        .eq("codigo", codigo.strip().upper())
        .eq("ativo", True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not dados:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado no catálogo comercial.")
    return dados[0]


def _reconciliar_modelos_sem_interromper_operacao() -> None:
    try:
        reconciliar_modelos_com_storage(executor="CTI_BACKEND_CATALOGO")
    except Exception as exc:
        print(f"[CATALOGO] [AVISO] Reconciliação automática de modelos pendente: {exc}")


@router.get("/equipamentos")
def listar_equipamentos(linha: str | None = None):
    _reconciliar_modelos_sem_interromper_operacao()
    consulta = supabase.table("cti_catalogo_equipamentos").select("*").eq("ativo", True)
    if linha:
        consulta = consulta.eq("linha_produto", linha.strip().upper())
    equipamentos = consulta.order("linha_produto").order("ordem").order("nome_comercial").execute().data or []
    return [{**item, "preco_vigente": _preco_vigente(str(item["codigo"]))} for item in equipamentos]


@router.get("/equipamentos/{codigo}")
def detalhe_equipamento(codigo: str):
    equipamento = _equipamento(codigo)
    return {**equipamento, "preco_vigente": _preco_vigente(str(equipamento["codigo"]))}


@router.get("/precos-vigentes")
def listar_precos_vigentes():
    return listar_equipamentos()


@router.post("/oportunidades/{oportunidade_id}/itens")
def criar_item_por_catalogo(oportunidade_id: str, dados: CriarItemCatalogoRequest):
    oportunidades = supabase.table("cti_oportunidades").select("id").eq("id", oportunidade_id).limit(1).execute().data or []
    if not oportunidades:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")

    equipamento = _equipamento(dados.equipamento_codigo)
    preco = _preco_vigente(str(equipamento["codigo"]))
    if not preco:
        raise HTTPException(status_code=422, detail="O equipamento não possui tabela de preço vigente.")

    preco_cheio = float(preco.get("preco_cheio") or 0)
    payload = {
        "oportunidade_id": oportunidade_id,
        "equipamento_codigo": equipamento["codigo"],
        "linha_produto": equipamento["linha_produto"],
        "modelo_base": equipamento["modelo_base"],
        "nome_comercial": equipamento["nome_comercial"],
        "equipamento": equipamento["nome_comercial"],
        "configuracao": equipamento["configuracao"],
        "compressor": equipamento.get("compressor"),
        "possui_eletrico": bool(equipamento.get("possui_eletrico")),
        "preco_tabela": preco_cheio,
        "preco_unitario": preco_cheio,
        "tabela_preco_codigo": preco.get("tabela_codigo"),
        "tabela_preco_vigencia": preco.get("vigencia_inicio"),
        "quantidade": dados.quantidade,
        "desconto_percentual": dados.desconto_percentual,
        "condicao_pagamento": dados.condicao_pagamento,
        "prazo_entrega": dados.prazo_entrega,
        "validade_condicao": dados.validade_condicao,
        "frete": dados.frete,
        "local_entrega": dados.local_entrega,
        "garantia": dados.garantia,
        "opcionais": dados.opcionais,
        "observacoes_comerciais": dados.observacoes_comerciais,
        "observacoes_tecnicas": dados.observacoes_tecnicas,
        "ordem": dados.ordem,
        "updated_at": _agora(),
    }
    return supabase.table("cti_oportunidade_itens").insert(payload).execute().data or []
