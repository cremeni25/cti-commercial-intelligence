from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.supabase_client import supabase


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def valor_item(item: dict[str, Any]) -> float:
    quantidade = float(item.get("quantidade") or 0)
    preco = float(item.get("preco_unitario") or item.get("preco_tabela") or 0)
    desconto = float(item.get("desconto_percentual") or 0)
    return round(quantidade * preco * (1 - desconto / 100), 2)


def sincronizar_resumo_oportunidade(oportunidade_id: str) -> dict[str, Any]:
    itens = (
        supabase.table("cti_oportunidade_itens")
        .select("nome_comercial,equipamento,quantidade,preco_unitario,preco_tabela,desconto_percentual,status,ordem,created_at")
        .eq("oportunidade_id", oportunidade_id)
        .order("ordem")
        .order("created_at")
        .execute()
        .data
        or []
    )
    ativos = [item for item in itens if str(item.get("status") or "").upper() not in {"CANCELADO", "PERDIDO"}]
    total = round(sum(valor_item(item) for item in ativos), 2)
    equipamentos = [str(item.get("nome_comercial") or item.get("equipamento") or "").strip() for item in ativos]
    equipamentos = [item for item in equipamentos if item]
    supabase.table("cti_oportunidades").update({"valor_estimado": total, "updated_at": _agora()}).eq("id", oportunidade_id).execute()
    return {"valor_total": total, "equipamentos": equipamentos, "quantidade_itens": len(ativos)}
