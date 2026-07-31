from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import PurePosixPath

from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from core.supabase_client import supabase

router = APIRouter(prefix="/modelos-proposta-storage", tags=["Modelos de proposta"])

BUCKET = "modelos-propostas-carrier"
ALLOWED_MIME = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validar_token(token: str | None) -> None:
    esperado = os.getenv("CTI_TEMPLATE_UPLOAD_TOKEN", "").strip()
    if not esperado:
        raise HTTPException(status_code=503, detail="Carregamento de templates ainda não habilitado no servidor.")
    if not token or token != esperado:
        raise HTTPException(status_code=401, detail="Credencial de carregamento inválida.")


def _modelo(modelo_id: str) -> dict:
    dados = (
        supabase.table("cti_modelos_proposta")
        .select("*")
        .eq("id", modelo_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not dados:
        raise HTTPException(status_code=404, detail="Modelo de proposta não encontrado.")
    return dados[0]


@router.get("/status")
def status_modelos():
    modelos = (
        supabase.table("cti_modelos_proposta")
        .select(
            "id,linha_produto,equipamento,versao,arquivo_template_nome_original,"
            "arquivo_template_tamanho_bytes,arquivo_template_hash_sha256,"
            "arquivo_template_storage,homologado_em,ativo"
        )
        .eq("ativo", True)
        .order("linha_produto")
        .order("equipamento")
        .execute()
        .data
        or []
    )
    return {
        "bucket": BUCKET,
        "total": len(modelos),
        "armazenados": sum(1 for item in modelos if item.get("arquivo_template_storage")),
        "homologados": sum(1 for item in modelos if item.get("homologado_em")),
        "modelos": modelos,
    }


@router.post("/{modelo_id}/carregar")
async def carregar_template(
    modelo_id: str,
    arquivo: UploadFile = File(...),
    x_cti_template_token: str | None = Header(default=None),
):
    _validar_token(x_cti_template_token)
    modelo = _modelo(modelo_id)

    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(status_code=422, detail="Arquivo vazio.")

    nome_recebido = PurePosixPath(arquivo.filename or "").name
    nome_esperado = str(modelo.get("arquivo_template_nome_original") or "")
    mime = arquivo.content_type or "application/octet-stream"
    tamanho = len(conteudo)
    hash_recebido = hashlib.sha256(conteudo).hexdigest()

    if nome_recebido != nome_esperado:
        raise HTTPException(status_code=422, detail=f"Nome divergente. Esperado: {nome_esperado}")
    if mime not in ALLOWED_MIME:
        raise HTTPException(status_code=422, detail="Tipo de arquivo não permitido.")
    if tamanho != int(modelo.get("arquivo_template_tamanho_bytes") or 0):
        raise HTTPException(status_code=422, detail="Tamanho do arquivo divergente do original registrado.")
    if hash_recebido.lower() != str(modelo.get("arquivo_template_hash_sha256") or "").lower():
        raise HTTPException(status_code=422, detail="SHA-256 divergente. O arquivo não corresponde ao original Carrier.")

    linha = str(modelo.get("linha_produto") or "").lower().replace(" ", "-")
    equipamento = str(modelo.get("equipamento") or "").lower().replace(" ", "-")
    versao = int(modelo.get("versao") or 1)
    caminho = f"{linha}/{equipamento}/v{versao}/{nome_recebido}"

    if modelo.get("arquivo_template_storage"):
        raise HTTPException(status_code=409, detail="Este modelo já possui arquivo mestre armazenado.")

    resposta = supabase.storage.from_(BUCKET).upload(
        caminho,
        conteudo,
        {"content-type": mime, "upsert": "false"},
    )
    if not resposta:
        raise HTTPException(status_code=502, detail="O Supabase não confirmou o armazenamento do arquivo.")

    atualizado = (
        supabase.table("cti_modelos_proposta")
        .update({
            "arquivo_template_storage": caminho,
            "homologado_em": _agora(),
            "layout_preservado": True,
            "conteudo_integral_obrigatorio": True,
            "imutavel": True,
            "updated_at": _agora(),
        })
        .eq("id", modelo_id)
        .execute()
        .data
        or []
    )

    supabase.table("cti_modelos_proposta_auditoria").insert({
        "modelo_proposta_id": modelo_id,
        "operacao": "HOMOLOGACAO",
        "versao": versao,
        "arquivo_template_storage": caminho,
        "arquivo_template_nome_original": nome_recebido,
        "arquivo_template_hash_sha256": hash_recebido,
        "conteudo_template": modelo.get("conteudo_template") or {},
        "justificativa": "Arquivo original Carrier validado por nome, MIME, tamanho e SHA-256 antes do armazenamento privado.",
    }).execute()

    return {
        "ok": True,
        "modelo_id": modelo_id,
        "caminho": caminho,
        "sha256": hash_recebido,
        "registro": atualizado,
    }
