from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-documentos", tags=["Propostas - primeira página"])


class PrimeiraPaginaUpdate(BaseModel):
    voltagem: str | None = None
    tipo_equipamento: str | None = None
    impostos: str | None = None
    acessorios: str | None = None
    condicao_pagamento: str | None = None
    possui_entrada: bool | None = None
    valor_entrada: float | None = Field(default=None, ge=0)
    local_entrega: str | None = None
    autorizada_nome_endereco: str | None = None
    frete: str | None = None
    prazo_entrega: str | None = None
    validade: str | None = None
    lynx_meses: int | None = Field(default=None, ge=0)


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    rows = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not rows:
        raise HTTPException(status_code=404, detail=detalhe)
    return rows[0]


def _normalizar(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.strip().split())
    return value or None


def _snapshot(proposta: dict[str, Any]) -> dict[str, Any]:
    raw = proposta.get("snapshot_dados")
    return dict(raw) if isinstance(raw, dict) else {}


def _documento_final(proposta: dict[str, Any]) -> dict[str, Any]:
    snapshot = _snapshot(proposta)
    raw = snapshot.get("documento_final")
    return dict(raw) if isinstance(raw, dict) else {}


def _contexto(proposta_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada.")
    item_id = str(proposta.get("item_oportunidade_id") or "").strip()
    if not item_id:
        raise HTTPException(status_code=409, detail="A proposta não possui item comercial vinculado.")
    item = _primeiro("cti_oportunidade_itens", item_id, "Item comercial da proposta não encontrado.")
    return proposta, item


def _valor(final: dict[str, Any], item: dict[str, Any], chave_final: str, *chaves_item: str) -> Any:
    if chave_final in final and final.get(chave_final) not in {None, ""}:
        return final.get(chave_final)
    for chave in chaves_item:
        valor = item.get(chave)
        if valor not in {None, ""}:
            return valor
    return None


def _editavel(proposta: dict[str, Any]) -> bool:
    snapshot = _snapshot(proposta)
    arquivo = snapshot.get("arquivo_documento")
    return not (isinstance(arquivo, dict) and arquivo.get("path") and arquivo.get("sha256"))


@router.get("/propostas/{proposta_id}/primeira-pagina")
def consultar_primeira_pagina(proposta_id: str):
    proposta, item = _contexto(proposta_id)
    final = _documento_final(proposta)
    return {
        "proposta_id": proposta_id,
        "item_id": item.get("id"),
        "equipamento": item.get("equipamento"),
        "editavel": _editavel(proposta),
        "campos": {
            "voltagem": _valor(final, item, "voltagem"),
            "tipo_equipamento": _valor(final, item, "tipo_equipamento", "configuracao", "tipo_equipamento"),
            "impostos": _valor(final, item, "impostos") or "04% ICMS/PIS/COFINS",
            "acessorios": _valor(final, item, "acessorios", "acessorios") or (
                ", ".join(str(v) for v in (item.get("opcionais") or [])) if isinstance(item.get("opcionais"), list) else item.get("opcionais")
            ),
            "condicao_pagamento": _valor(final, item, "condicao_pagamento", "condicao_pagamento"),
            "possui_entrada": final.get("possui_entrada"),
            "valor_entrada": final.get("valor_entrada"),
            "local_entrega": _valor(final, item, "local_entrega", "local_entrega", "tipo_entrega"),
            "autorizada_nome_endereco": final.get("autorizada_nome_endereco"),
            "frete": _valor(final, item, "frete", "frete"),
            "prazo_entrega": _valor(final, item, "prazo_entrega", "prazo_entrega"),
            "validade": _valor(final, item, "validade", "validade_condicao"),
            "lynx_meses": final.get("lynx_meses"),
        },
        "valores_negociados": {
            "quantidade": item.get("quantidade") or 1,
            "preco_unitario": item.get("preco_unitario"),
            "desconto_percentual": item.get("desconto_percentual"),
            "valor_proposta": proposta.get("valor"),
        },
    }


@router.put("/propostas/{proposta_id}/primeira-pagina")
def atualizar_primeira_pagina(proposta_id: str, dados: PrimeiraPaginaUpdate):
    proposta, _item = _contexto(proposta_id)
    if not _editavel(proposta):
        raise HTTPException(
            status_code=409,
            detail="O documento oficial já foi finalizado e tornou-se imutável. Os dados não podem mais ser alterados.",
        )

    supplied = dados.model_dump(exclude_unset=True)
    snapshot = _snapshot(proposta)
    final = _documento_final(proposta)

    campos_texto = {
        "voltagem",
        "tipo_equipamento",
        "impostos",
        "acessorios",
        "condicao_pagamento",
        "local_entrega",
        "autorizada_nome_endereco",
        "frete",
        "prazo_entrega",
        "validade",
    }
    for chave, valor in supplied.items():
        if chave in campos_texto:
            final[chave] = _normalizar(valor)
        else:
            final[chave] = valor

    final["atualizado_em"] = _agora()
    snapshot["documento_final"] = final

    updated = (
        supabase.table("cti_propostas")
        .update({"snapshot_dados": snapshot})
        .eq("id", proposta_id)
        .execute()
        .data
        or []
    )
    if not updated:
        raise HTTPException(status_code=409, detail="O banco não confirmou a atualização dos dados finais do documento.")

    return {
        "ok": True,
        "proposta_id": proposta_id,
        "editavel": True,
        "campos": final,
    }
