from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.supabase_client import supabase
from services.email_transport_service import configuracao_email
from services.proposal_document_repository import FINAL_BUCKET, MASTER_BUCKET
from services.proposal_template_catalog import TEMPLATES

router = APIRouter(prefix="/crm-documentos", tags=["Validação operacional documental"])


def _status_bucket(bucket: str) -> dict[str, Any]:
    try:
        resposta = supabase.storage.from_(bucket).list(path="", options={"limit": 1})
        return {"ok": True, "bucket": bucket, "acessivel": resposta is not None}
    except Exception as exc:
        return {"ok": False, "bucket": bucket, "erro": str(exc)}


@router.get("/validacao-operacional")
def validacao_operacional_documentos():
    esperados = {item.equipment for item in TEMPLATES}
    try:
        modelos = (
            supabase.table("cti_modelos_proposta")
            .select(
                "id,equipamento,versao,ativo,arquivo_template_storage,"
                "arquivo_template_hash_sha256,homologado_em"
            )
            .eq("ativo", True)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        return {
            "operacional": False,
            "etapa": "BANCO",
            "bloqueios": [f"Falha ao consultar cti_modelos_proposta: {exc}"],
        }

    por_equipamento = {str(item.get("equipamento") or "").strip().upper(): item for item in modelos}
    ausentes = sorted(esperados - set(por_equipamento))
    sem_arquivo = sorted(
        equipamento
        for equipamento in esperados
        if equipamento in por_equipamento
        and not por_equipamento[equipamento].get("arquivo_template_storage")
    )
    sem_hash = sorted(
        equipamento
        for equipamento in esperados
        if equipamento in por_equipamento
        and not por_equipamento[equipamento].get("arquivo_template_hash_sha256")
    )
    nao_homologados = sorted(
        equipamento
        for equipamento in esperados
        if equipamento in por_equipamento
        and not por_equipamento[equipamento].get("homologado_em")
    )

    bucket_mestres = _status_bucket(MASTER_BUCKET)
    bucket_finais = _status_bucket(FINAL_BUCKET)
    email = configuracao_email()

    bloqueios: list[str] = []
    if ausentes:
        bloqueios.append(f"Modelos ausentes: {', '.join(ausentes)}")
    if sem_arquivo:
        bloqueios.append(f"Arquivos mestres não carregados: {', '.join(sem_arquivo)}")
    if sem_hash:
        bloqueios.append(f"Hashes não registrados: {', '.join(sem_hash)}")
    if nao_homologados:
        bloqueios.append(f"Modelos ainda não homologados: {', '.join(nao_homologados)}")
    if not bucket_mestres.get("ok"):
        bloqueios.append(f"Bucket mestre indisponível: {bucket_mestres.get('erro')}")
    if not bucket_finais.get("ok"):
        bloqueios.append(f"Bucket final indisponível: {bucket_finais.get('erro')}")
    if not email.get("configurado"):
        bloqueios.append("Transporte de e-mail não configurado no Render.")

    return {
        "operacional": not bloqueios,
        "modelos": {
            "esperados": len(esperados),
            "ativos_encontrados": len(set(por_equipamento) & esperados),
            "ausentes": ausentes,
            "sem_arquivo": sem_arquivo,
            "sem_hash": sem_hash,
            "nao_homologados": nao_homologados,
        },
        "storage": {
            "mestres": bucket_mestres,
            "documentos_finais": bucket_finais,
        },
        "email": {
            "configurado": bool(email.get("configurado")),
            "remetente": email.get("remetente"),
            "reply_to_configurado": bool(email.get("reply_to")),
        },
        "bloqueios": bloqueios,
        "proxima_acao": (
            "Executar uma proposta real completa: finalizar documento, abrir/baixar, aceitar, converter em pedido e enviar o e-mail com anexo."
            if not bloqueios
            else "Resolver somente os bloqueios listados; não há outra rodada de validação interna antes do teste real."
        ),
    }
