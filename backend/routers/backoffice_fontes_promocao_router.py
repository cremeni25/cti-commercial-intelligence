from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.ingestion_promotion import promover_item, validar_lote
from core.supabase_client import supabase

router = APIRouter(prefix="/backoffice-fontes", tags=["Back Office Promoção"])


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _admin_master(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario != "ADMIN_MASTER" and not usuario.permissoes.get("acesso_total"):
        raise HTTPException(status_code=403, detail="Promoção operacional restrita ao ADMIN_MASTER.")
    return usuario


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if isinstance(dados, dict):
        return [dados]
    return []


def _evento(fonte_id: str, evento: str, usuario_id: str, detalhes: dict[str, Any]) -> None:
    supabase.table("cti_fontes_eventos").insert({
        "fonte_id": fonte_id,
        "evento": evento,
        "detalhes": detalhes,
        "usuario_id": usuario_id,
    }).execute()


@router.post("/{fonte_id}/reconciliacao/promover")
def promover_reconciliacao(fonte_id: str, usuario: UsuarioAutenticado = Depends(_admin_master)):
    fontes = _dados(supabase.table("cti_fontes_universais").select("id,nome_arquivo").eq("id", fonte_id).limit(1).execute())
    if not fontes:
        raise HTTPException(status_code=404, detail="Fonte não encontrada.")
    fonte = fontes[0]

    recs = _dados(supabase.table("cti_fontes_reconciliacoes").select("*").eq("fonte_id", fonte_id).limit(1).execute())
    if not recs:
        raise HTTPException(status_code=404, detail="Reconciliação não preparada.")
    rec = recs[0]

    itens = _dados(
        supabase.table("cti_fontes_reconciliacao_itens")
        .select("*")
        .eq("reconciliacao_id", rec["id"])
        .order("indice_semantico")
        .execute()
    )
    try:
        validacao = validar_lote(rec, itens)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not validacao["aprovado"]:
        raise HTTPException(status_code=409, detail={"mensagem": "Lote bloqueado para promoção.", "bloqueios": validacao["bloqueios"]})

    tentativa = _dados(supabase.table("cti_fontes_promocoes").insert({
        "fonte_id": fonte_id,
        "reconciliacao_id": rec["id"],
        "dominio_alvo": rec["dominio_alvo"],
        "status": "EM_EXECUCAO",
        "total_itens": len(itens),
        "executado_por": usuario.id,
    }).execute())[0]

    resultados: list[dict[str, Any]] = []
    agora = _agora()
    try:
        for item in itens:
            resultado = promover_item(str(rec["dominio_alvo"]), item, fonte_nome=str(fonte.get("nome_arquivo") or ""))
            resultados.append({"item_id": item["id"], "indice_semantico": item["indice_semantico"], "resultado": resultado})
            supabase.table("cti_fontes_reconciliacao_itens").update({"status_item": "PROMOVIDO", "updated_at": agora}).eq("id", item["id"]).execute()

        supabase.table("cti_fontes_reconciliacoes").update({
            "status": "PROMOVIDA",
            "updated_at": agora,
            "detalhes": {**(rec.get("detalhes") or {}), "promocao_id": tentativa["id"], "regra_promocao": "CTI_PROMOCAO_CONTROLADA_V1"},
        }).eq("id", rec["id"]).execute()
        supabase.table("cti_fontes_promocoes").update({
            "status": "CONCLUIDA",
            "total_promovidos": len(resultados),
            "resultado": {"itens": resultados},
            "concluido_em": agora,
        }).eq("id", tentativa["id"]).execute()
        _evento(fonte_id, "PROMOCAO_OPERACIONAL_CONCLUIDA", usuario.id, {
            "promocao_id": tentativa["id"],
            "dominio_alvo": rec["dominio_alvo"],
            "total_promovidos": len(resultados),
        })
        return {
            "promocao_id": tentativa["id"],
            "status": "CONCLUIDA",
            "dominio_alvo": rec["dominio_alvo"],
            "total_promovidos": len(resultados),
            "resultados": resultados,
        }
    except Exception as exc:
        supabase.table("cti_fontes_reconciliacoes").update({"status": "ERRO", "updated_at": _agora()}).eq("id", rec["id"]).execute()
        supabase.table("cti_fontes_promocoes").update({
            "status": "ERRO",
            "total_promovidos": len(resultados),
            "resultado": {"itens_concluidos": resultados, "erro": str(exc)[:1000]},
            "concluido_em": _agora(),
        }).eq("id", tentativa["id"]).execute()
        _evento(fonte_id, "PROMOCAO_OPERACIONAL_ERRO", usuario.id, {"promocao_id": tentativa["id"], "erro": str(exc)[:500]})
        raise HTTPException(status_code=500, detail="Promoção interrompida e registrada para auditoria. Itens já promovidos permanecem rastreados e idempotentes.") from exc
