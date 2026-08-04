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


def convert_docx_to_pdf(docx: bytes, filename: str, *, expected_pages: int = 4) -> ConvertedPdf:
    if not docx:
        raise DocxPdfConversionError("Documento DOCX vazio.")

    url, key = _converter_config()
    safe_filename = Path(filename or "proposta.docx").name
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
            headers={"X-CTI-Converter-Key": key},
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
