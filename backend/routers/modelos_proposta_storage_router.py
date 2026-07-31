from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timezone
from pathlib import PurePosixPath

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.supabase_client import supabase

router = APIRouter(prefix="/modelos-proposta-storage", tags=["Modelos de proposta"])

BUCKET = "modelos-propostas-carrier"
ALLOWED_MIME = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class HomologacaoTemplate(BaseModel):
    sha256_confirmado: str
    validacao_visual_integral: bool
    observacao: str | None = None


class HomologacaoLoteItem(BaseModel):
    modelo_id: str
    sha256_confirmado: str
    validacao_visual_integral: bool
    observacao: str | None = None


class HomologacaoLote(BaseModel):
    itens: list[HomologacaoLoteItem] = Field(min_length=1, max_length=50)


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validar_token(token: str | None) -> None:
    esperado = os.getenv("CTI_TEMPLATE_UPLOAD_TOKEN", "").strip()
    if not esperado:
        raise HTTPException(status_code=503, detail="Gestão de templates ainda não habilitada no servidor.")
    if not token or not hmac.compare_digest(token, esperado):
        raise HTTPException(status_code=401, detail="Credencial de gestão de templates inválida.")


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


def _baixar_e_validar_arquivo_armazenado(modelo: dict) -> tuple[bytes, str]:
    caminho = str(modelo.get("arquivo_template_storage") or "").strip()
    if not caminho:
        raise HTTPException(status_code=409, detail="O arquivo mestre ainda não foi armazenado.")

    try:
        conteudo = supabase.storage.from_(BUCKET).download(caminho)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível recuperar o arquivo mestre do bucket privado.",
        ) from exc

    if not conteudo:
        raise HTTPException(status_code=502, detail="O arquivo mestre armazenado está vazio ou indisponível.")

    hash_storage = hashlib.sha256(conteudo).hexdigest().lower()
    hash_esperado = str(modelo.get("arquivo_template_hash_sha256") or "").lower()
    tamanho_esperado = int(modelo.get("arquivo_template_tamanho_bytes") or 0)

    if len(conteudo) != tamanho_esperado:
        raise HTTPException(
            status_code=409,
            detail="O tamanho do arquivo armazenado diverge do original Carrier registrado.",
        )
    if not hmac.compare_digest(hash_storage, hash_esperado):
        raise HTTPException(
            status_code=409,
            detail="O SHA-256 do arquivo armazenado diverge do original Carrier registrado.",
        )

    return conteudo, hash_storage


def _url_temporaria(caminho: str, validade_segundos: int = 900) -> str:
    try:
        resposta = supabase.storage.from_(BUCKET).create_signed_url(caminho, validade_segundos)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível criar o acesso temporário ao arquivo mestre.",
        ) from exc

    if isinstance(resposta, dict):
        url = resposta.get("signedURL") or resposta.get("signed_url")
    else:
        url = getattr(resposta, "signed_url", None) or getattr(resposta, "signedURL", None)

    if not url:
        raise HTTPException(status_code=502, detail="O Supabase não retornou a URL temporária do arquivo.")
    return str(url)


def _homologar_modelo(modelo: dict, dados: HomologacaoTemplate) -> dict:
    modelo_id = str(modelo.get("id"))
    if modelo.get("homologado_em"):
        raise HTTPException(status_code=409, detail="Este modelo já está homologado.")
    if not dados.validacao_visual_integral:
        raise HTTPException(status_code=422, detail="A validação visual integral é obrigatória.")

    _, hash_storage = _baixar_e_validar_arquivo_armazenado(modelo)
    hash_confirmado = dados.sha256_confirmado.lower()
    if not hmac.compare_digest(hash_confirmado, hash_storage):
        raise HTTPException(status_code=422, detail="SHA-256 de confirmação divergente.")

    agora = _agora()
    atualizado = (
        supabase.table("cti_modelos_proposta")
        .update({"homologado_em": agora, "updated_at": agora})
        .eq("id", modelo_id)
        .is_("homologado_em", "null")
        .execute()
        .data
        or []
    )
    if not atualizado:
        raise HTTPException(status_code=409, detail="O modelo foi homologado ou alterado por outro processo.")

    supabase.table("cti_modelos_proposta_auditoria").insert({
        "modelo_proposta_id": modelo_id,
        "operacao": "HOMOLOGACAO",
        "versao": int(modelo.get("versao") or 1),
        "arquivo_template_storage": modelo.get("arquivo_template_storage"),
        "arquivo_template_nome_original": modelo.get("arquivo_template_nome_original"),
        "arquivo_template_hash_sha256": hash_storage,
        "conteudo_template": modelo.get("conteudo_template") or {},
        "justificativa": dados.observacao or "Validação visual integral confirmada sem alteração do padrão Carrier, após nova conferência do binário armazenado no bucket privado.",
    }).execute()

    return {
        "ok": True,
        "modelo_id": modelo_id,
        "homologado_em": agora,
        "sha256_storage_validado": hash_storage,
        "registro": atualizado,
    }


@router.get("/status")
def status_modelos(x_cti_template_token: str | None = Header(default=None)):
    _validar_token(x_cti_template_token)
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


@router.get("/fila-homologacao")
def fila_homologacao(
    validade_segundos: int = 900,
    x_cti_template_token: str | None = Header(default=None),
):
    _validar_token(x_cti_template_token)
    validade = max(60, min(validade_segundos, 1800))
    modelos = (
        supabase.table("cti_modelos_proposta")
        .select(
            "id,linha_produto,equipamento,versao,arquivo_template_nome_original,"
            "arquivo_template_tamanho_bytes,arquivo_template_hash_sha256,"
            "arquivo_template_storage,homologado_em,ativo"
        )
        .eq("ativo", True)
        .not_.is_("arquivo_template_storage", "null")
        .is_("homologado_em", "null")
        .order("linha_produto")
        .order("equipamento")
        .execute()
        .data
        or []
    )

    fila = []
    for modelo in modelos:
        caminho = str(modelo.get("arquivo_template_storage") or "")
        fila.append({
            **modelo,
            "url_temporaria": _url_temporaria(caminho, validade),
            "url_valida_por_segundos": validade,
            "situacao": "PENDENTE_VALIDACAO_VISUAL",
        })

    return {"total_pendente": len(fila), "fila": fila}


@router.post("/homologar-lote")
def homologar_lote(
    dados: HomologacaoLote,
    x_cti_template_token: str | None = Header(default=None),
):
    _validar_token(x_cti_template_token)
    resultados = []
    erros = []

    ids = [item.modelo_id for item in dados.itens]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="O lote contém modelo_id duplicado.")

    for item in dados.itens:
        try:
            modelo = _modelo(item.modelo_id)
            resultado = _homologar_modelo(
                modelo,
                HomologacaoTemplate(
                    sha256_confirmado=item.sha256_confirmado,
                    validacao_visual_integral=item.validacao_visual_integral,
                    observacao=item.observacao,
                ),
            )
            resultados.append(resultado)
        except HTTPException as exc:
            erros.append({
                "modelo_id": item.modelo_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
            })

    return {
        "ok": not erros,
        "homologados": len(resultados),
        "falhas": len(erros),
        "resultados": resultados,
        "erros": erros,
    }


@router.post("/{modelo_id}/carregar")
async def carregar_template(
    modelo_id: str,
    arquivo: UploadFile = File(...),
    x_cti_template_token: str | None = Header(default=None),
):
    _validar_token(x_cti_template_token)
    modelo = _modelo(modelo_id)

    if modelo.get("arquivo_template_storage"):
        raise HTTPException(status_code=409, detail="Este modelo já possui arquivo mestre armazenado.")

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
    if not hmac.compare_digest(
        hash_recebido.lower(),
        str(modelo.get("arquivo_template_hash_sha256") or "").lower(),
    ):
        raise HTTPException(status_code=422, detail="SHA-256 divergente. O arquivo não corresponde ao original Carrier.")

    linha = str(modelo.get("linha_produto") or "").lower().replace(" ", "-")
    equipamento = str(modelo.get("equipamento") or "").lower().replace(" ", "-")
    versao = int(modelo.get("versao") or 1)
    caminho = f"{linha}/{equipamento}/v{versao}/{nome_recebido}"

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
            "homologado_em": None,
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
        "operacao": "ATIVACAO",
        "versao": versao,
        "arquivo_template_storage": caminho,
        "arquivo_template_nome_original": nome_recebido,
        "arquivo_template_hash_sha256": hash_recebido,
        "conteudo_template": modelo.get("conteudo_template") or {},
        "justificativa": "Arquivo original Carrier validado por nome, MIME, tamanho e SHA-256 e armazenado em bucket privado. Homologação visual ainda pendente.",
    }).execute()

    return {
        "ok": True,
        "modelo_id": modelo_id,
        "caminho": caminho,
        "sha256": hash_recebido,
        "homologado": False,
        "registro": atualizado,
    }


@router.post("/{modelo_id}/homologar")
def homologar_template(
    modelo_id: str,
    dados: HomologacaoTemplate,
    x_cti_template_token: str | None = Header(default=None),
):
    _validar_token(x_cti_template_token)
    modelo = _modelo(modelo_id)
    return _homologar_modelo(modelo, dados)
