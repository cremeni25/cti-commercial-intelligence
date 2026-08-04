from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


class DocxPdfConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConvertedPdf:
    filename: str
    content: bytes
    sha256: str
    page_count: int


def _libreoffice_binary() -> str:
    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if not binary:
        raise DocxPdfConversionError(
            "LibreOffice não está instalado no ambiente. A conversão por Pandoc foi desativada porque altera layout, imagens e paginação."
        )
    return binary


def _convert_with_libreoffice(source: Path, workdir: Path) -> Path:
    command = [
        _libreoffice_binary(),
        "--headless",
        "--nologo",
        "--nodefault",
        "--nofirststartwizard",
        "--nolockcheck",
        "--convert-to",
        "pdf:writer_pdf_Export",
        "--outdir",
        str(workdir),
        str(source),
    ]
    try:
        result = subprocess.run(
            command,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            env={"HOME": str(workdir)},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DocxPdfConversionError(f"Falha ao iniciar o LibreOffice: {exc}") from exc

    output = workdir / f"{source.stem}.pdf"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "erro sem detalhe").strip()
        raise DocxPdfConversionError(f"LibreOffice recusou a conversão: {detail[:800]}")
    if not output.exists() or output.stat().st_size == 0:
        detail = (result.stderr or result.stdout or "arquivo não produzido").strip()
        raise DocxPdfConversionError(f"LibreOffice não produziu o PDF esperado: {detail[:800]}")
    return output


def convert_docx_to_pdf(docx: bytes, filename: str, *, expected_pages: int = 4) -> ConvertedPdf:
    if not docx:
        raise DocxPdfConversionError("Documento DOCX vazio.")

    stem = Path(filename or "proposta.docx").stem or "proposta"
    with tempfile.TemporaryDirectory(prefix="cti-proposta-") as temp_dir:
        workdir = Path(temp_dir)
        source = workdir / f"{stem}.docx"
        source.write_bytes(docx)
        output = _convert_with_libreoffice(source, workdir)
        content = output.read_bytes()

    try:
        page_count = len(PdfReader(io_stream := __import__("io").BytesIO(content)).pages)
        io_stream.close()
    except Exception as exc:
        raise DocxPdfConversionError(f"Não foi possível validar a paginação do PDF: {exc}") from exc

    if expected_pages > 0 and page_count != expected_pages:
        raise DocxPdfConversionError(
            f"PDF bloqueado: o mestre oficial possui {expected_pages} páginas, mas a conversão produziu {page_count}."
        )

    return ConvertedPdf(
        filename=f"{stem}.pdf",
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        page_count=page_count,
    )
