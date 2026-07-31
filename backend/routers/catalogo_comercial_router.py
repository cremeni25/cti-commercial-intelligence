from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase

router = APIRouter(prefix="/catalogo-comercial", tags=["Catálogo Comercial"])


@router.get("/equipamentos")
def listar_equipamentos(linha: str | None = None):
    consulta = supabase.table("cti_catalogo_equipamentos").select("*").eq("ativo", True)
    if linha:
        consulta = consulta.eq("linha_produto", linha.strip().upper())
    return consulta.order("linha_produto").order("ordem").order("nome_comercial").execute().data or []


@router.get("/equipamentos/{codigo}")
def detalhe_equipamento(codigo: str):
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
    equipamento = dados[0]
    precos = (
        supabase.table("cti_tabela_precos")
        .select("*")
        .eq("equipamento_codigo", equipamento["codigo"])
        .eq("ativo", True)
        .lte("vigencia_inicio", date.today().isoformat())
        .order("vigencia_inicio", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    equipamento["preco_vigente"] = precos[0] if precos else None
    return equipamento


@router.get("/precos-vigentes")
def listar_precos_vigentes():
    equipamentos = listar_equipamentos()
    resultado: list[dict[str, Any]] = []
    for equipamento in equipamentos:
        preco = (
            supabase.table("cti_tabela_precos")
            .select("*")
            .eq("equipamento_codigo", equipamento["codigo"])
            .eq("ativo", True)
            .lte("vigencia_inicio", date.today().isoformat())
            .order("vigencia_inicio", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        resultado.append({**equipamento, "preco_vigente": preco[0] if preco else None})
    return resultado
