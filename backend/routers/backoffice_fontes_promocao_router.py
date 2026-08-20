from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

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


def detalhes_conflito_promocao(item: dict[str, Any], erro: Exception) -> list[dict[str, Any]]:
    base = {
        "tipo": "DIVERGENCIA_PROMOCAO",
        "item_id": item.get("id"),
        "indice_semantico": item.get("indice_semantico"),
        "entidade": item.get("entidade_sugerida"),
        "natureza_canonica": item.get("natureza_canonica"),
        "mensagem": str(erro)[:1000],
        "regra": "CTI_PROMOCAO_CONFLITO_RASTREAVEL_V2_ESTRUTURADO",
    }
    conflitos = getattr(erro, "conflitos", None)
    if isinstance(conflitos, list):
        estruturados = []
        for conflito in conflitos:
            if isinstance(conflito, dict):
                estruturados.append({**base, **conflito})
        if estruturados:
            return estruturados
    return [base]


def detalhe_conflito_promocao(item: dict[str, Any], erro: Exception) -> dict[str, Any]:
    return detalhes_conflito_promocao(item, erro)[0]


@router.post("/{fonte_id}/reconciliacao/promover")
def promover_reconciliacao(
    fonte_id: str,
    natureza: str | None = Query(default=None, max_length=80),
    usuario: UsuarioAutenticado = Depends(_admin_master),
):
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
        validacao = validar_lote(rec, itens, natureza_alvo=natureza)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not validacao["aprovado"]:
        raise HTTPException(status_code=409, detail={
            "mensagem": "Lote bloqueado para promoção.",
            "bloqueios": validacao["bloqueios"],
            "naturezas_disponiveis": validacao.get("naturezas_disponiveis", []),
        })

    itens_promocao = list(validacao.get("itens") or [])
    natureza_alvo = str(validacao.get("natureza_alvo") or "")

    tentativa = _dados(supabase.table("cti_fontes_promocoes").insert({
        "fonte_id": fonte_id,
        "reconciliacao_id": rec["id"],
        "dominio_alvo": rec["dominio_alvo"],
        "status": "EM_EXECUCAO",
        "total_itens": len(itens_promocao),
        "executado_por": usuario.id,
        "resultado": {"natureza_alvo": natureza_alvo},
    }).execute())[0]

    resultados: list[dict[str, Any]] = []
    agora = _agora()
    try:
        for item in itens_promocao:
            try:
                resultado = promover_item(str(rec["dominio_alvo"]), item, fonte_nome=str(fonte.get("nome_arquivo") or ""))
            except ValueError as exc:
                conflitos = detalhes_conflito_promocao(item, exc)
                conflito = conflitos[0]
                supabase.table("cti_fontes_reconciliacao_itens").update({
                    "status_item": "CONFLITO",
                    "conflitos": conflitos,
                    "updated_at": _agora(),
                }).eq("id", item["id"]).execute()
                supabase.table("cti_fontes_reconciliacoes").update({
                    "status": "EM_REVISAO",
                    "total_conflitos": int(rec.get("total_conflitos") or 0) + 1,
                    "updated_at": _agora(),
                    "detalhes": {
                        **(rec.get("detalhes") or {}),
                        "ultimo_conflito_promocao": conflito,
                        "regra_promocao": "CTI_PROMOCAO_CONFLITO_RASTREAVEL_V2_ESTRUTURADO",
                    },
                }).eq("id", rec["id"]).execute()
                supabase.table("cti_fontes_promocoes").update({
                    "status": "ERRO",
                    "total_promovidos": len(resultados),
                    "resultado": {
                        "natureza_alvo": natureza_alvo,
                        "tipo": "CONFLITO_RECONCILIACAO",
                        "conflito": conflito,
                        "conflitos": conflitos,
                        "itens_concluidos": resultados,
                    },
                    "concluido_em": _agora(),
                }).eq("id", tentativa["id"]).execute()
                _evento(fonte_id, "PROMOCAO_BLOQUEADA_CONFLITO", usuario.id, {
                    "promocao_id": tentativa["id"],
                    "natureza_alvo": natureza_alvo,
                    "conflito": conflito,
                    "conflitos": conflitos,
                    "total_promovidos_antes_bloqueio": len(resultados),
                })
                raise HTTPException(status_code=409, detail={
                    "mensagem": "Promoção bloqueada por divergência. O item retornou para reconciliação e nenhum dado divergente foi sobrescrito.",
                    "promocao_id": tentativa["id"],
                    "conflito": conflito,
                    "conflitos": conflitos,
                    "total_promovidos_antes_bloqueio": len(resultados),
                }) from exc

            resultados.append({
                "item_id": item["id"],
                "indice_semantico": item["indice_semantico"],
                "natureza_canonica": item.get("natureza_canonica"),
                "resultado": resultado,
            })
            supabase.table("cti_fontes_reconciliacao_itens").update({"status_item": "PROMOVIDO", "updated_at": agora}).eq("id", item["id"]).execute()

        restantes = _dados(
            supabase.table("cti_fontes_reconciliacao_itens")
            .select("id,status_item,natureza_canonica")
            .eq("reconciliacao_id", rec["id"])
            .eq("status_item", "PRONTO_PROMOCAO")
            .execute()
        )
        status_rec = "PROMOCAO_PARCIAL" if restantes else "PROMOVIDA"
        supabase.table("cti_fontes_reconciliacoes").update({
            "status": status_rec,
            "updated_at": agora,
            "detalhes": {
                **(rec.get("detalhes") or {}),
                "promocao_id": tentativa["id"],
                "regra_promocao": "CTI_PROMOCAO_CONTROLADA_V3_MERGE_SEGURO",
                "ultima_natureza_promovida": natureza_alvo,
                "itens_restantes": len(restantes),
            },
        }).eq("id", rec["id"]).execute()
        supabase.table("cti_fontes_promocoes").update({
            "status": "CONCLUIDA",
            "total_promovidos": len(resultados),
            "resultado": {
                "natureza_alvo": natureza_alvo,
                "itens": resultados,
                "itens_restantes": len(restantes),
            },
            "concluido_em": agora,
        }).eq("id", tentativa["id"]).execute()
        _evento(fonte_id, "PROMOCAO_OPERACIONAL_CONCLUIDA", usuario.id, {
            "promocao_id": tentativa["id"],
            "dominio_alvo": rec["dominio_alvo"],
            "natureza_alvo": natureza_alvo,
            "total_promovidos": len(resultados),
            "itens_restantes": len(restantes),
        })
        return {
            "promocao_id": tentativa["id"],
            "status": "CONCLUIDA",
            "status_reconciliacao": status_rec,
            "dominio_alvo": rec["dominio_alvo"],
            "natureza_alvo": natureza_alvo,
            "total_promovidos": len(resultados),
            "itens_restantes": len(restantes),
            "resultados": resultados,
        }
    except HTTPException:
        raise
    except Exception as exc:
        supabase.table("cti_fontes_reconciliacoes").update({"status": "ERRO", "updated_at": _agora()}).eq("id", rec["id"]).execute()
        supabase.table("cti_fontes_promocoes").update({
            "status": "ERRO",
            "total_promovidos": len(resultados),
            "resultado": {"natureza_alvo": natureza_alvo, "itens_concluidos": resultados, "erro": str(exc)[:1000]},
            "concluido_em": _agora(),
        }).eq("id", tentativa["id"]).execute()
        _evento(fonte_id, "PROMOCAO_OPERACIONAL_ERRO", usuario.id, {
            "promocao_id": tentativa["id"],
            "natureza_alvo": natureza_alvo,
            "erro": str(exc)[:500],
        })
        raise HTTPException(status_code=500, detail="Promoção interrompida e registrada para auditoria. Itens já promovidos permanecem rastreados e idempotentes.") from exc
