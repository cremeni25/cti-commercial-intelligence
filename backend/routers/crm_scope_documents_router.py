from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_router import _proposta_autorizada
from routers.propostas_documentos_oficiais_router import _build_preview, _filename_ascii
from services.proposal_document_repository import DOCX_MIME, ProposalDocumentRepositoryError

secure_router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro"])
public_router = APIRouter(prefix="/documentos-preview", tags=["Preview documental temporário"])

PREVIEW_TTL_SECONDS = 300


def _segredo_preview() -> bytes:
    segredo = (
        os.getenv("CTI_DOCUMENT_PREVIEW_SECRET", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    if not segredo:
        raise HTTPException(status_code=503, detail="Assinatura temporária de documentos não configurada.")
    return segredo.encode("utf-8")


def _assinatura(proposta_id: str, expira_em: int) -> str:
    mensagem = f"{proposta_id}:{expira_em}".encode("utf-8")
    digest = hmac.new(_segredo_preview(), mensagem, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _validar_assinatura(proposta_id: str, expira_em: int, assinatura: str) -> None:
    agora = int(time.time())
    if expira_em < agora or expira_em > agora + (PREVIEW_TTL_SECONDS + 60):
        raise HTTPException(status_code=403, detail="Acesso temporário ao documento expirado.")
    esperado = _assinatura(proposta_id, expira_em)
    if not hmac.compare_digest(esperado, str(assinatura or "")):
        raise HTTPException(status_code=403, detail="Assinatura do documento inválida.")


def _preview(proposta_id: str) -> dict:
    try:
        return _build_preview(proposta_id)
    except HTTPException:
        raise
    except ProposalDocumentRepositoryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao preparar o Word oficial: {type(exc).__name__}: {exc}") from exc


@secure_router.get("/propostas/{proposta_id}/previsualizar-documento")
def previsualizar_documento_seguro(
    proposta_id: str,
    request: Request,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _proposta_autorizada(proposta_id, usuario)
    preview = _preview(proposta_id)
    sha256 = str(preview.get("sha256") or "").strip()
    if not sha256:
        raise HTTPException(status_code=409, detail="O Word preenchido foi gerado sem SHA-256.")

    expira_em = int(time.time()) + PREVIEW_TTL_SECONDS
    assinatura = _assinatura(proposta_id, expira_em)
    arquivo_url = str(request.url_for("preview_documento_assinado", proposta_id=proposta_id))
    arquivo_url += f"?expira_em={expira_em}&assinatura={quote(assinatura, safe='')}&v={sha256[:16]}"
    viewer_url = "https://view.officeapps.live.com/op/embed.aspx?src=" + quote(arquivo_url, safe="")
    return {
        "proposal_id": proposta_id,
        "filename": _filename_ascii(str(preview.get("filename") or ""), proposta_id),
        "mime_type": DOCX_MIME,
        "sha256": sha256,
        "document_url": arquivo_url,
        "viewer_url": viewer_url,
        "expires_in": PREVIEW_TTL_SECONDS,
        "preview_mode": str(preview.get("preview_mode") or "WORD_PREENCHIDO"),
    }


@public_router.get("/propostas/{proposta_id}/arquivo", name="preview_documento_assinado")
def preview_documento_assinado(
    proposta_id: str,
    expira_em: int = Query(...),
    assinatura: str = Query(..., min_length=16),
):
    _validar_assinatura(proposta_id, expira_em, assinatura)
    preview = _preview(proposta_id)
    content = bytes(preview.get("content") or b"")
    if not content:
        raise HTTPException(status_code=409, detail="O Word preenchido foi gerado sem conteúdo.")
    filename = _filename_ascii(str(preview.get("filename") or ""), proposta_id)
    return StreamingResponse(
        BytesIO(content),
        media_type=DOCX_MIME,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(content)),
            "Cache-Control": "private, max-age=300",
            "X-Content-Type-Options": "nosniff",
            "X-CTI-Document-Mode": str(preview.get("preview_mode") or "WORD_PREENCHIDO"),
            "X-CTI-SHA256": str(preview.get("sha256") or ""),
        },
    )
