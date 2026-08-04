from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class DocxPdfConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConvertedPdf:
    filename: str
    content: bytes
    sha256: str


def _converter_command(source: Path, output: Path) -> list[str]:
    pandoc = shutil.which("pandoc")
    prince = shutil.which("prince") or shutil.which("princexml")
    if not pandoc or not prince:
        missing = []
        if not pandoc:
            missing.append("pandoc")
        if not prince:
            missing.append("princexml")
        raise DocxPdfConversionError(
            "Conversor PDF indisponível no ambiente: " + ", ".join(missing)
        )
    return [
        pandoc,
        str(source),
        "--from=docx",
        "--pdf-engine",
        prince,
        "--output",
        str(output),
    ]


def convert_docx_to_pdf(docx: bytes, filename: str) -> ConvertedPdf:
    if not docx:
        raise DocxPdfConversionError("Documento DOCX vazio.")
    stem = Path(filename or "proposta.docx").stem or "proposta"
    with tempfile.TemporaryDirectory(prefix="cti-proposta-") as temp_dir:
        workdir = Path(temp_dir)
        source = workdir / f"{stem}.docx"
        output = workdir / f"{stem}.pdf"
        source.write_bytes(docx)
        command = _converter_command(source, output)
        try:
            result = subprocess.run(
                command,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise DocxPdfConversionError(f"Falha ao iniciar a conversão PDF: {exc}") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro sem detalhe").strip()
            raise DocxPdfConversionError(f"Conversão PDF recusada: {detail[:500]}")
        if not output.exists() or output.stat().st_size == 0:
            raise DocxPdfConversionError("O conversor não produziu o PDF esperado.")
        content = output.read_bytes()
    return ConvertedPdf(
        filename=f"{stem}.pdf",
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
    )
