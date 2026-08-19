from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.ingestion_reconciliation import avaliar_item, pode_aprovar, preparar_plano
from core.supabase_client import supabase

router = APIRouter(prefix="/backoffice-fontes", tags=["Back Office Reconciliação"])


class ResolucaoConflitoRequest(BaseModel):
    dados_normalizados: dict[str, Any]
    motivo: str = Field(min_length=3, max_length=500)


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _admin_master(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario != "ADMIN_MASTER" and not usuario.permissoes.get("acesso_total"):
        raise HTTPException(status_code=403, detail="Reconciliação restrita ao ADMIN_MASTER.")
    return usuario


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if isinstance(dados, dict):
        return [dados]
    return []


def _fonte(fonte_id: str) -> dict[str, Any]:
    linhas = _dados(supabase.table("cti_fontes_universais").select("*").eq("id", fonte_id).limit(1).execute())
    if not linhas:
        raise HTTPException(status_code=404, detail="Fonte não encontrada.")
    return linhas[0]


def _evento(fonte_id: str, evento: str, usuario_id: str, detalhes: dict[str, Any]) -> None:
    supabase.table("cti_fontes_eventos").insert({
        "fonte_id": fonte_id,
        "evento": evento,
        "detalhes": detalhes,
        "usuario_id": usuario_id,
    }).execute()


def avaliar_resolucao_conflito(classificacao: str, item: dict[str, Any], dados_normalizados: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(dados_normalizados, dict) or not dados_normalizados:
        raise ValueError("Resolução exige dados corrigidos estruturados.")
    reavaliado = avaliar_item(
        classificacao,
        {
            "indice": item.get("indice_semantico"),
            "dados": dados_normalizados,
        },
    )
    if reavaliado.get("status_item") != "VALIDO" or reavaliado.get("conflitos"):
        raise ValueError("Dados corrigidos ainda possuem conflito semântico e não podem retornar para promoção.")
    return reavaliado


@router.post("/{fonte_id}/reconciliacao/preparar")
def preparar_reconciliacao(fonte_id: str, usuario: UsuarioAutenticado = Depends(_admin_master)):
    fonte = _fonte(fonte_id)
    destino = (fonte.get("metadados") or {}).get("destino_ingestao") if isinstance(fonte.get("metadados"), dict) else None
    if not isinstance(destino, dict) or destino.get("destino") != "CANDIDATO_OPERACIONAL_VALIDACAO":
        raise HTTPException(status_code=409, detail="Fonte não classificada como candidata operacional.")

    registros = _dados(
        supabase.table("cti_fontes_semanticas")
        .select("indice,dados,conteudo_texto,metadados")
        .eq("fonte_id", fonte_id)
        .order("indice")
        .execute()
    )
    if not registros:
        raise HTTPException(status_code=409, detail="Fonte sem registros semânticos para reconciliar.")

    plano = preparar_plano(str(destino.get("classificacao") or fonte.get("classificacao_sugerida") or ""), registros)
    existente = _dados(supabase.table("cti_fontes_reconciliacoes").select("*").eq("fonte_id", fonte_id).limit(1).execute())
    payload_rec = {
        "fonte_id": fonte_id,
        "classificacao": plano["classificacao"],
        "dominio_alvo": plano["dominio_alvo"],
        "status": "EM_REVISAO" if plano["total_conflitos"] else "PREPARADA",
        "total_itens": plano["total_itens"],
        "total_validos": plano["total_validos"],
        "total_conflitos": plano["total_conflitos"],
        "promocao_operacional_automatica": False,
        "detalhes": {"regra": plano["regra"], "origem": "BACKOFFICE_FONTES"},
        "criado_por": usuario.id,
        "updated_at": _agora(),
    }
    if existente:
        rec = _dados(supabase.table("cti_fontes_reconciliacoes").update(payload_rec).eq("id", existente[0]["id"]).execute())[0]
        supabase.table("cti_fontes_reconciliacao_itens").delete().eq("reconciliacao_id", rec["id"]).execute()
    else:
        rec = _dados(supabase.table("cti_fontes_reconciliacoes").insert(payload_rec).execute())[0]

    itens = []
    for item in plano["itens"]:
        itens.append({**item, "reconciliacao_id": rec["id"], "fonte_id": fonte_id})
    if itens:
        for inicio in range(0, len(itens), 500):
            supabase.table("cti_fontes_reconciliacao_itens").insert(itens[inicio:inicio + 500]).execute()

    _evento(fonte_id, "RECONCILIACAO_PREPARADA", usuario.id, {
        "reconciliacao_id": rec["id"],
        "dominio_alvo": plano["dominio_alvo"],
        "total_itens": plano["total_itens"],
        "total_conflitos": plano["total_conflitos"],
    })
    return {"reconciliacao": rec, "resumo": plano | {"itens": plano["itens"][:50]}}


@router.get("/{fonte_id}/reconciliacao")
def consultar_reconciliacao(fonte_id: str, usuario: UsuarioAutenticado = Depends(_admin_master)):
    _fonte(fonte_id)
    recs = _dados(supabase.table("cti_fontes_reconciliacoes").select("*").eq("fonte_id", fonte_id).limit(1).execute())
    if not recs:
        return {"reconciliacao": None, "itens": []}
    rec = recs[0]
    itens = _dados(
        supabase.table("cti_fontes_reconciliacao_itens")
        .select("*")
        .eq("reconciliacao_id", rec["id"])
        .order("indice_semantico")
        .limit(500)
        .execute()
    )
    return {"reconciliacao": rec, "itens": itens}


@router.post("/{fonte_id}/reconciliacao/itens/{item_id}/resolver")
def resolver_conflito_reconciliacao(
    fonte_id: str,
    item_id: str,
    payload: ResolucaoConflitoRequest,
    usuario: UsuarioAutenticado = Depends(_admin_master),
):
    _fonte(fonte_id)
    recs = _dados(supabase.table("cti_fontes_reconciliacoes").select("*").eq("fonte_id", fonte_id).limit(1).execute())
    if not recs:
        raise HTTPException(status_code=404, detail="Reconciliação não preparada.")
    rec = recs[0]
    itens = _dados(
        supabase.table("cti_fontes_reconciliacao_itens")
        .select("*")
        .eq("id", item_id)
        .eq("reconciliacao_id", rec["id"])
        .limit(1)
        .execute()
    )
    if not itens:
        raise HTTPException(status_code=404, detail="Item de reconciliação não encontrado.")
    item = itens[0]
    if str(item.get("status_item") or "") != "CONFLITO":
        raise HTTPException(status_code=409, detail="Somente item em CONFLITO pode ser resolvido por esta ação.")

    try:
        reavaliado = avaliar_resolucao_conflito(rec["classificacao"], item, payload.dados_normalizados)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    agora = _agora()
    atualizado = _dados(
        supabase.table("cti_fontes_reconciliacao_itens").update({
            "entidade_sugerida": reavaliado["entidade_sugerida"],
            "natureza_canonica": reavaliado["natureza_canonica"],
            "camada_dashboard": reavaliado["camada_dashboard"],
            "acao_sugerida": reavaliado["acao_sugerida"],
            "chave_canonica": reavaliado["chave_canonica"],
            "dados_normalizados": reavaliado["dados_normalizados"],
            "conflitos": [],
            "status_item": "VALIDO",
            "updated_at": agora,
        }).eq("id", item_id).execute()
    )[0]

    conflitos_restantes = _dados(
        supabase.table("cti_fontes_reconciliacao_itens")
        .select("id")
        .eq("reconciliacao_id", rec["id"])
        .eq("status_item", "CONFLITO")
        .execute()
    )
    total_conflitos = len(conflitos_restantes)
    total_itens = int(rec.get("total_itens") or 0)
    status_rec = "PREPARADA" if total_conflitos == 0 else "EM_REVISAO"
    detalhes = dict(rec.get("detalhes") or {})
    detalhes["ultima_resolucao_conflito"] = {
        "item_id": item_id,
        "motivo": payload.motivo,
        "resolvido_por": usuario.id,
        "resolvido_em": agora,
        "regra": "CTI_RECONCILIACAO_RESOLUCAO_CONFLITO_V1",
    }
    rec_atualizada = _dados(
        supabase.table("cti_fontes_reconciliacoes").update({
            "status": status_rec,
            "total_conflitos": total_conflitos,
            "total_validos": max(total_itens - total_conflitos, 0),
            "aprovado_por": None,
            "aprovado_em": None,
            "detalhes": detalhes,
            "updated_at": agora,
        }).eq("id", rec["id"]).execute()
    )[0]

    _evento(fonte_id, "RECONCILIACAO_CONFLITO_RESOLVIDO", usuario.id, {
        "reconciliacao_id": rec["id"],
        "item_id": item_id,
        "motivo": payload.motivo,
        "conflitos_restantes": total_conflitos,
        "requer_nova_aprovacao": True,
    })
    return {
        "reconciliacao": rec_atualizada,
        "item": atualizado,
        "conflitos_restantes": total_conflitos,
        "requer_nova_aprovacao": True,
        "pronto_para_aprovacao": total_conflitos == 0,
    }


@router.post("/{fonte_id}/reconciliacao/aprovar")
def aprovar_reconciliacao(fonte_id: str, usuario: UsuarioAutenticado = Depends(_admin_master)):
    _fonte(fonte_id)
    recs = _dados(supabase.table("cti_fontes_reconciliacoes").select("*").eq("fonte_id", fonte_id).limit(1).execute())
    if not recs:
        raise HTTPException(status_code=404, detail="Reconciliação não preparada.")
    rec = recs[0]
    if not pode_aprovar(rec):
        raise HTTPException(status_code=409, detail="Reconciliação possui conflitos ou não está pronta para aprovação.")

    agora = _agora()
    atualizado = _dados(
        supabase.table("cti_fontes_reconciliacoes").update({
            "status": "PRONTO_PROMOCAO",
            "aprovado_por": usuario.id,
            "aprovado_em": agora,
            "updated_at": agora,
        }).eq("id", rec["id"]).execute()
    )[0]
    supabase.table("cti_fontes_reconciliacao_itens").update({"status_item": "PRONTO_PROMOCAO", "updated_at": agora}).eq("reconciliacao_id", rec["id"]).eq("status_item", "VALIDO").execute()
    _evento(fonte_id, "RECONCILIACAO_APROVADA", usuario.id, {
        "reconciliacao_id": rec["id"],
        "dominio_alvo": rec["dominio_alvo"],
        "promocao_executada": False,
    })
    return {
        "reconciliacao": atualizado,
        "pronto_promocao": True,
        "promocao_executada": False,
        "mensagem": "Reconciliação aprovada. Registros continuam em staging até o adaptador do domínio executar promoção controlada.",
    }
