from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from services.universal_source_interpreter import interpretar_fonte
from services.universal_source_semantics import interpretar_semanticamente

router = APIRouter(prefix="/backoffice-fontes", tags=["Back Office Universal de Fontes"])

BUCKET = "cti-fontes-universais"
MAX_BYTES = 50 * 1024 * 1024

TIPOS_EXTENSAO = {
    ".pdf": "PDF", ".doc": "WORD", ".docx": "WORD", ".ppt": "POWERPOINT", ".pptx": "POWERPOINT",
    ".xls": "PLANILHA", ".xlsx": "PLANILHA", ".csv": "PLANILHA", ".ods": "PLANILHA",
    ".txt": "TEXTO", ".md": "TEXTO", ".json": "DADOS_ESTRUTURADOS", ".xml": "DADOS_ESTRUTURADOS",
    ".png": "IMAGEM", ".jpg": "IMAGEM", ".jpeg": "IMAGEM", ".webp": "IMAGEM", ".tif": "IMAGEM", ".tiff": "IMAGEM",
}

TRANSICOES_ADMIN = {
    "RECEBIDO": {"REJEITADO"},
    "INTERPRETADO": {"VALIDADO", "REJEITADO"},
    "VALIDADO": {"HOMOLOGADO", "REJEITADO"},
    "HOMOLOGADO": {"PUBLICADO_IA", "REJEITADO"},
    "PUBLICADO_IA": {"REJEITADO"},
    "ERRO": {"REJEITADO"},
    "REJEITADO": set(),
}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _admin_master(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario != "ADMIN_MASTER" and not usuario.permissoes.get("acesso_total"):
        raise HTTPException(status_code=403, detail="Back Office Universal restrito ao ADMIN_MASTER.")
    return usuario


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    if isinstance(dados, list): return [item for item in dados if isinstance(item, dict)]
    if isinstance(dados, dict): return [dados]
    return []


def _nome_seguro(nome: str) -> str:
    nome = Path(nome or "arquivo").name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", nome).strip(".-")
    return stem[:180] or "arquivo"


def _tipo_detectado(nome: str, mime_type: str | None) -> tuple[str, str]:
    extensao = Path(nome).suffix.lower()
    tipo = TIPOS_EXTENSAO.get(extensao)
    if tipo: return tipo, extensao
    mime = str(mime_type or "").lower()
    if mime.startswith("image/"): return "IMAGEM", extensao
    if mime.startswith("text/"): return "TEXTO", extensao
    return "DESCONHECIDO", extensao


def _registrar_evento(fonte_id: str, evento: str, usuario_id: str, *, anterior: str | None = None, novo: str | None = None, detalhes: dict[str, Any] | None = None) -> None:
    supabase.table("cti_fontes_eventos").insert({"fonte_id": fonte_id, "evento": evento, "status_anterior": anterior, "status_novo": novo, "detalhes": detalhes or {}, "usuario_id": usuario_id}).execute()


class AtualizarGovernancaRequest(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    classificacao_negocio: str | None = Field(default=None, max_length=80)
    observacao: str | None = Field(default=None, max_length=2000)


@router.get("")
def listar_fontes(usuario: UsuarioAutenticado = Depends(_admin_master)):
    linhas = _dados(supabase.table("cti_fontes_universais").select("*").order("created_at", desc=True).limit(500).execute())
    contagens: dict[str, int] = {}
    for item in linhas:
        status = str(item.get("status_governanca") or "DESCONHECIDO")
        contagens[status] = contagens.get(status, 0) + 1
    return {"fontes": linhas, "total": len(linhas), "por_status": contagens, "modo": "governanca_admin_master"}


@router.get("/{fonte_id}")
def detalhar_fonte(fonte_id: str, usuario: UsuarioAutenticado = Depends(_admin_master)):
    fonte = _dados(supabase.table("cti_fontes_universais").select("*").eq("id", fonte_id).limit(1).execute())
    if not fonte: raise HTTPException(status_code=404, detail="Fonte não encontrada.")
    eventos = _dados(supabase.table("cti_fontes_eventos").select("*").eq("fonte_id", fonte_id).order("created_at", desc=True).execute())
    preview = _dados(supabase.table("cti_fontes_semanticas").select("indice,tipo_registro,conteudo_texto,dados,metadados").eq("fonte_id", fonte_id).order("indice").limit(30).execute())
    return {"fonte": fonte[0], "eventos": eventos, "preview_semantico": preview}


@router.post("/upload")
async def receber_fonte(arquivo: UploadFile = File(...), usuario: UsuarioAutenticado = Depends(_admin_master)):
    nome_original = _nome_seguro(arquivo.filename or "arquivo")
    conteudo = await arquivo.read(MAX_BYTES + 1)
    if not conteudo: raise HTTPException(status_code=400, detail="Arquivo vazio.")
    if len(conteudo) > MAX_BYTES: raise HTTPException(status_code=413, detail="Arquivo excede o limite de 50 MB desta execução.")
    digest = sha256(conteudo).hexdigest()
    existente = _dados(supabase.table("cti_fontes_universais").select("*").eq("sha256", digest).limit(1).execute())
    if existente: return {"fonte": existente[0], "duplicado": True, "mensagem": "Fonte já registrada; nenhum arquivo duplicado foi criado."}
    tipo, extensao = _tipo_detectado(nome_original, arquivo.content_type)
    fonte_id = str(uuid4())
    storage_path = f"recebidos/{fonte_id}/{nome_original}"
    try:
        supabase.storage.from_(BUCKET).upload(storage_path, conteudo, file_options={"content-type": arquivo.content_type or "application/octet-stream", "upsert": "false"})
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível preservar o arquivo original no armazenamento privado.") from exc
    payload = {"id": fonte_id, "nome_arquivo": nome_original, "nome_exibicao": nome_original, "mime_type": arquivo.content_type, "extensao": extensao, "tamanho_bytes": len(conteudo), "sha256": digest, "storage_bucket": BUCKET, "storage_path": storage_path, "tipo_detectado": tipo, "classificacao_negocio": "NAO_CLASSIFICADA", "status_governanca": "RECEBIDO", "interpretacao_resumo": {"etapa": "METADADOS_IDENTIFICADOS", "tipo_arquivo": tipo, "mensagem": "Original preservado. Conteúdo ainda não foi homologado nem publicado para a IA."}, "metadados": {"mime_declarado": arquivo.content_type, "nome_original": arquivo.filename}, "publicado_ia": False, "criado_por": usuario.id}
    try:
        criado = _dados(supabase.table("cti_fontes_universais").insert(payload).execute())
        if not criado: raise RuntimeError("Registro da fonte não retornado.")
        _registrar_evento(fonte_id, "FONTE_RECEBIDA", usuario.id, novo="RECEBIDO", detalhes={"sha256": digest, "tipo_detectado": tipo, "tamanho_bytes": len(conteudo)})
    except Exception as exc:
        try: supabase.storage.from_(BUCKET).remove([storage_path])
        except Exception: pass
        raise HTTPException(status_code=500, detail="Falha ao registrar a governança da fonte.") from exc
    return {"fonte": criado[0], "duplicado": False}


@router.post("/{fonte_id}/interpretar")
def interpretar_fonte_recebida(fonte_id: str, usuario: UsuarioAutenticado = Depends(_admin_master)):
    atual = _dados(supabase.table("cti_fontes_universais").select("*").eq("id", fonte_id).limit(1).execute())
    if not atual: raise HTTPException(status_code=404, detail="Fonte não encontrada.")
    fonte = atual[0]
    if str(fonte.get("status_governanca") or "") != "RECEBIDO": raise HTTPException(status_code=409, detail="Somente fontes RECEBIDAS podem iniciar interpretação.")
    try:
        conteudo = supabase.storage.from_(str(fonte.get("storage_bucket") or BUCKET)).download(str(fonte.get("storage_path") or ""))
        estrutural = interpretar_fonte(str(fonte.get("nome_arquivo") or "arquivo"), str(fonte.get("tipo_detectado") or "DESCONHECIDO"), conteudo)
        semantica = interpretar_semanticamente(str(fonte.get("nome_arquivo") or "arquivo"), str(fonte.get("tipo_detectado") or "DESCONHECIDO"), conteudo)
        supabase.table("cti_fontes_semanticas").delete().eq("fonte_id", fonte_id).execute()
        lotes = []
        for registro in semantica["registros"]:
            lotes.append({"fonte_id": fonte_id, **registro})
            if len(lotes) >= 250:
                supabase.table("cti_fontes_semanticas").insert(lotes).execute(); lotes = []
        if lotes: supabase.table("cti_fontes_semanticas").insert(lotes).execute()
        resumo = {**estrutural, "semantica": {k: v for k, v in semantica.items() if k not in {"registros", "preview"}}, "preview": semantica["preview"]}
        alteracoes = {"status_governanca": "INTERPRETADO", "interpretacao_resumo": resumo, "classificacao_sugerida": semantica["classificacao_sugerida"], "confianca_classificacao": semantica["confianca_classificacao"], "descricao_semantica": semantica["descricao_semantica"], "campos_semanticos": semantica["campos_semanticos"], "interpretado_semanticamente_em": _agora(), "updated_at": _agora()}
        atualizado = _dados(supabase.table("cti_fontes_universais").update(alteracoes).eq("id", fonte_id).execute())
        _registrar_evento(fonte_id, "FONTE_INTERPRETADA_SEMANTICAMENTE", usuario.id, anterior="RECEBIDO", novo="INTERPRETADO", detalhes={"classificacao": semantica["classificacao_sugerida"], "confianca": semantica["confianca_classificacao"], "registros": semantica["total_registros_semanticos"]})
        return {"fonte": atualizado[0] if atualizado else {**fonte, **alteracoes}, "preview_semantico": semantica["preview"]}
    except HTTPException: raise
    except Exception as exc:
        try:
            supabase.table("cti_fontes_universais").update({"status_governanca": "ERRO", "alertas": [{"tipo": "INTERPRETACAO", "mensagem": str(exc)[:500]}], "updated_at": _agora()}).eq("id", fonte_id).execute()
            _registrar_evento(fonte_id, "ERRO_INTERPRETACAO", usuario.id, anterior="RECEBIDO", novo="ERRO")
        except Exception: pass
        raise HTTPException(status_code=500, detail="A fonte foi preservada, mas a interpretação não foi concluída.") from exc


@router.patch("/{fonte_id}/governanca")
def atualizar_governanca(fonte_id: str, request: AtualizarGovernancaRequest, usuario: UsuarioAutenticado = Depends(_admin_master)):
    atual = _dados(supabase.table("cti_fontes_universais").select("*").eq("id", fonte_id).limit(1).execute())
    if not atual: raise HTTPException(status_code=404, detail="Fonte não encontrada.")
    fonte = atual[0]
    anterior = str(fonte.get("status_governanca") or "")
    novo = request.status.strip().upper()
    if novo not in TRANSICOES_ADMIN.get(anterior, set()): raise HTTPException(status_code=409, detail=f"Transição {anterior} → {novo} não é permitida pelo gate atual de governança.")
    alteracoes: dict[str, Any] = {"status_governanca": novo, "updated_at": _agora()}
    if request.classificacao_negocio: alteracoes["classificacao_negocio"] = request.classificacao_negocio.strip().upper()
    elif novo in {"VALIDADO", "HOMOLOGADO"} and str(fonte.get("classificacao_negocio") or "") == "NAO_CLASSIFICADA": alteracoes["classificacao_negocio"] = str(fonte.get("classificacao_sugerida") or "DOCUMENTO_GERAL")
    if novo == "HOMOLOGADO": alteracoes.update({"homologado_por": usuario.id, "homologado_em": _agora()})
    if novo == "PUBLICADO_IA": alteracoes.update({"publicado_ia": True, "publicado_ia_em": _agora()})
    atualizado = _dados(supabase.table("cti_fontes_universais").update(alteracoes).eq("id", fonte_id).execute())
    _registrar_evento(fonte_id, "GOVERNANCA_ATUALIZADA", usuario.id, anterior=anterior, novo=novo, detalhes={"observacao": request.observacao, "classificacao_negocio": request.classificacao_negocio})
    return {"fonte": atualizado[0] if atualizado else {**fonte, **alteracoes}}
