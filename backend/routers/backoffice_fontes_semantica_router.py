from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.ingestion_destination import decidir_destino
from core.supabase_client import supabase
from services.universal_semantic_source import gerar_semantica

router = APIRouter(prefix="/backoffice-fontes", tags=["Back Office Universal de Fontes"])


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _admin_master(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario != "ADMIN_MASTER" and not usuario.permissoes.get("acesso_total"):
        raise HTTPException(status_code=403, detail="Back Office Universal restrito ao ADMIN_MASTER.")
    return usuario


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if isinstance(dados, dict):
        return [dados]
    return []


def _fonte(fonte_id: str) -> dict[str, Any]:
    registros = _dados(
        supabase.table("cti_fontes_universais")
        .select("*")
        .eq("id", fonte_id)
        .limit(1)
        .execute()
    )
    if not registros:
        raise HTTPException(status_code=404, detail="Fonte não encontrada.")
    return registros[0]


def _evento(fonte_id: str, evento: str, usuario_id: str, detalhes: dict[str, Any] | None = None) -> None:
    supabase.table("cti_fontes_eventos").insert({
        "fonte_id": fonte_id,
        "evento": evento,
        "detalhes": detalhes or {},
        "usuario_id": usuario_id,
    }).execute()


@router.post("/{fonte_id}/semantica")
def interpretar_semanticamente(
    fonte_id: str,
    usuario: UsuarioAutenticado = Depends(_admin_master),
):
    fonte = _fonte(fonte_id)
    status = str(fonte.get("status_governanca") or "")
    if status not in {"INTERPRETADO", "VALIDADO", "HOMOLOGADO"}:
        raise HTTPException(status_code=409, detail="A interpretação semântica exige fonte previamente INTERPRETADA.")

    try:
        conteudo = supabase.storage.from_(str(fonte.get("storage_bucket") or "cti-fontes-universais")).download(
            str(fonte.get("storage_path") or "")
        )
        semantica = gerar_semantica(
            str(fonte.get("nome_arquivo") or "arquivo"),
            str(fonte.get("tipo_detectado") or "DESCONHECIDO"),
            conteudo,
            fonte.get("interpretacao_resumo") if isinstance(fonte.get("interpretacao_resumo"), dict) else {},
        )
        destino = decidir_destino(
            semantica["classificacao_sugerida"],
            semantica["confianca_classificacao"],
            entrada="BACKOFFICE_FONTES",
            possui_registros_semanticos=bool(semantica["registros"]),
        )

        supabase.table("cti_fontes_semanticas").delete().eq("fonte_id", fonte_id).execute()
        payload = []
        for item in semantica["registros"]:
            metadados = dict(item.get("metadados") or {})
            metadados["destino_canonico"] = destino["destino"]
            payload.append({
                "fonte_id": fonte_id,
                "indice": item["indice"],
                "tipo_registro": item["tipo_registro"],
                "conteudo_texto": item.get("conteudo_texto"),
                "dados": item.get("dados") or {},
                "metadados": metadados,
            })
        if payload:
            for inicio in range(0, len(payload), 500):
                supabase.table("cti_fontes_semanticas").insert(payload[inicio:inicio + 500]).execute()

        metadados_fonte = dict(fonte.get("metadados") or {})
        metadados_fonte["decisao_destino_canonico"] = destino
        alteracoes = {
            "classificacao_sugerida": semantica["classificacao_sugerida"],
            "confianca_classificacao": semantica["confianca_classificacao"],
            "descricao_semantica": semantica["descricao_semantica"],
            "campos_semanticos": semantica["campos_semanticos"],
            "metadados": metadados_fonte,
            "interpretado_semanticamente_em": _agora(),
            "updated_at": _agora(),
        }
        atualizado = _dados(
            supabase.table("cti_fontes_universais")
            .update(alteracoes)
            .eq("id", fonte_id)
            .execute()
        )
        _evento(
            fonte_id,
            "SEMANTICA_GERADA",
            usuario.id,
            {
                "classificacao_sugerida": semantica["classificacao_sugerida"],
                "confianca": semantica["confianca_classificacao"],
                "total_registros": semantica["total_registros"],
                "decisao_destino_canonico": destino,
            },
        )
        return {
            "fonte": atualizado[0] if atualizado else {**fonte, **alteracoes},
            "total_registros_semanticos": semantica["total_registros"],
            "preview": semantica["registros"][:20],
            "decisao_destino_canonico": destino,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="A fonte foi preservada, mas a interpretação semântica não foi concluída.") from exc


@router.get("/{fonte_id}/preview")
def preview_semantico(
    fonte_id: str,
    usuario: UsuarioAutenticado = Depends(_admin_master),
):
    fonte = _fonte(fonte_id)
    registros = _dados(
        supabase.table("cti_fontes_semanticas")
        .select("indice,tipo_registro,conteudo_texto,dados,metadados")
        .eq("fonte_id", fonte_id)
        .order("indice")
        .limit(100)
        .execute()
    )
    total = _dados(
        supabase.table("cti_fontes_semanticas")
        .select("id")
        .eq("fonte_id", fonte_id)
        .execute()
    )
    decisao = ((fonte.get("metadados") or {}).get("decisao_destino_canonico") if isinstance(fonte.get("metadados"), dict) else None)
    return {
        "fonte": fonte,
        "total_registros_semanticos": len(total),
        "preview": registros,
        "publicavel": str(fonte.get("status_governanca") or "") == "HOMOLOGADO" and bool(registros),
        "decisao_destino_canonico": decisao,
    }


@router.post("/{fonte_id}/publicar-ia")
def publicar_para_ia(
    fonte_id: str,
    usuario: UsuarioAutenticado = Depends(_admin_master),
):
    fonte = _fonte(fonte_id)
    if str(fonte.get("status_governanca") or "") != "HOMOLOGADO":
        raise HTTPException(status_code=409, detail="Somente fonte HOMOLOGADA pode ser publicada para a IA.")
    if not fonte.get("descricao_semantica") or not fonte.get("interpretado_semanticamente_em"):
        raise HTTPException(status_code=409, detail="Gere e revise a interpretação semântica antes da publicação.")
    amostra = _dados(
        supabase.table("cti_fontes_semanticas")
        .select("id")
        .eq("fonte_id", fonte_id)
        .limit(1)
        .execute()
    )
    if not amostra:
        raise HTTPException(status_code=409, detail="Fonte sem registros semânticos publicáveis.")

    atualizado = _dados(
        supabase.table("cti_fontes_universais")
        .update({
            "status_governanca": "PUBLICADO_IA",
            "publicado_ia": True,
            "publicado_ia_em": _agora(),
            "updated_at": _agora(),
        })
        .eq("id", fonte_id)
        .execute()
    )
    _evento(fonte_id, "FONTE_PUBLICADA_IA", usuario.id, {"escopo_ia": fonte.get("escopo_ia") or "ADMIN_MASTER"})
    return {
        "fonte": atualizado[0] if atualizado else fonte,
        "nome_catalogo_ia": f"fonte_{fonte_id.replace('-', '')}",
        "mensagem": "Fonte publicada dinamicamente para a IA Comercial; nenhuma alteração de código por documento foi necessária.",
    }
