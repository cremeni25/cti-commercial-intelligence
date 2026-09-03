from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import requests


class LegacyDocNormalizationError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedDocx:
    filename: str
    content: bytes


def _converter_config() -> tuple[str, str]:
    url = os.getenv("CTI_DOCUMENT_CONVERTER_URL", "").strip().rstrip("/")
    key = os.getenv("CTI_DOCUMENT_CONVERTER_KEY", "").strip()
    if not url or not key:
        raise LegacyDocNormalizationError("Serviço documental não configurado para normalizar DOC legado.")
    return url, key


def normalize_legacy_doc_to_docx(content: bytes, filename: str) -> NormalizedDocx:
    if not content:
        raise LegacyDocNormalizationError("Documento legado vazio.")
    safe_filename = Path(filename or "modelo.doc").name
    if not safe_filename.lower().endswith(".doc") or safe_filename.lower().endswith(".docx"):
        return NormalizedDocx(filename=safe_filename, content=content)

    url, key = _converter_config()
    try:
        response = requests.post(
            f"{url}/normalize-docx",
            files={"file": (safe_filename, content, "application/msword")},
            headers={"X-CTI-Converter-Key": key},
            timeout=210,
        )
    except requests.RequestException as exc:
        raise LegacyDocNormalizationError(f"Serviço documental indisponível: {exc}") from exc

    if response.status_code != 200:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text
        raise LegacyDocNormalizationError(
            f"Normalização DOC→DOCX recusada ({response.status_code}): {str(detail or 'sem detalhe')[:800]}"
        )

    normalized = bytes(response.content or b"")
    if not normalized.startswith(b"PK"):
        raise LegacyDocNormalizationError("O serviço documental não retornou um DOCX válido.")
    return NormalizedDocx(filename=f"{Path(safe_filename).stem}.docx", content=normalized)
