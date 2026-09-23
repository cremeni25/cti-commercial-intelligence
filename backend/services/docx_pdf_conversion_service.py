from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import requests
from pypdf import PdfReader


class DocxPdfConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConvertedPdf:
    filename: str
    content: bytes
    sha256: str
    page_count: int


def _converter_config() -> tuple[str, str]:
    url = os.getenv("CTI_DOCUMENT_CONVERTER_URL", "").strip().rstrip("/")
    key = os.getenv("CTI_DOCUMENT_CONVERTER_KEY", "").strip()
    if not url or not key:
        raise DocxPdfConversionError(
            "Serviço documental isolado não configurado. A conversão local foi desativada para proteger layout, imagens e paginação."
        )
    return url, key


_SOURCE_PAGE_CACHE: dict[str, int] = {}


def source_document_page_count(docx: bytes, filename: str) -> int:
    if not docx:
        raise DocxPdfConversionError("Documento mestre vazio.")
    digest = hashlib.sha256(docx).hexdigest()
    cached = _SOURCE_PAGE_CACHE.get(digest)
    if cached:
        return cached

    url, key = _converter_config()
    safe_filename = Path(filename or "modelo.docx").name
    try:
        response = requests.post(
            f"{url}/page-count",
            files={
                "file": (
                    safe_filename,
                    docx,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers={"X-CTI-Converter-Key": key},
            timeout=210,
        )
    except requests.RequestException as exc:
        raise DocxPdfConversionError(f"Serviço documental indisponível ao validar o mestre: {exc}") from exc

    if response.status_code != 200:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text
        raise DocxPdfConversionError(
            f"Não foi possível determinar a paginação do mestre ({response.status_code}): {str(detail or 'sem detalhe')[:800]}"
        )

    try:
        pages = int(response.json().get("pages") or 0)
    except Exception as exc:
        raise DocxPdfConversionError("O conversor não retornou uma paginação válida para o mestre.") from exc
    if pages <= 0:
        raise DocxPdfConversionError("O documento mestre não possui paginação válida.")

    _SOURCE_PAGE_CACHE[digest] = pages
    return pages


def convert_docx_to_pdf(docx: bytes, filename: str, *, expected_pages: int = 4) -> ConvertedPdf:
    if not docx:
        raise DocxPdfConversionError("Documento DOCX vazio.")

    url, key = _converter_config()
    safe_filename = Path(filename or "proposta.docx").name
    headers = {"X-CTI-Converter-Key": key}
    if expected_pages > 0:
        headers["X-CTI-Expected-Pages"] = str(expected_pages)
    try:
        response = requests.post(
            f"{url}/convert",
            files={
                "file": (
                    safe_filename,
                    docx,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers=headers,
            timeout=210,
        )
    except requests.RequestException as exc:
        raise DocxPdfConversionError(f"Serviço documental indisponível: {exc}") from exc

    if response.status_code != 200:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text
        raise DocxPdfConversionError(
            f"Conversão documental recusada ({response.status_code}): {str(detail or 'sem detalhe')[:800]}"
        )

    content = bytes(response.content or b"")
    if not content.startswith(b"%PDF"):
        raise DocxPdfConversionError("O serviço documental não retornou um PDF válido.")

    try:
        page_count = len(PdfReader(BytesIO(content)).pages)
    except Exception as exc:
        raise DocxPdfConversionError(f"Não foi possível validar a paginação do PDF: {exc}") from exc

    if expected_pages > 0 and page_count != expected_pages:
        raise DocxPdfConversionError(
            f"PDF bloqueado: o mestre oficial possui {expected_pages} páginas, mas a conversão produziu {page_count}."
        )

    stem = Path(safe_filename).stem or "proposta"
    return ConvertedPdf(
        filename=f"{stem}.pdf",
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        page_count=page_count,
    )
