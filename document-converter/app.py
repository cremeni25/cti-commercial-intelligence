from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from pypdf import PdfReader

app = FastAPI(title="CTI Document Converter", version="1.2.0")
EXPECTED_PAGES = 4
API_KEY = os.getenv("CTI_DOCUMENT_CONVERTER_KEY", "").strip()
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _authorize(value: str | None) -> None:
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Chave do conversor não configurada.")
    if value != API_KEY:
        raise HTTPException(status_code=401, detail="Acesso não autorizado.")


def _engine() -> tuple[str, str]:
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    xvfb = shutil.which("xvfb-run")
    if not executable or not xvfb:
        raise HTTPException(status_code=503, detail="Motor documental incompleto no serviço de conversão.")
    return executable, xvfb


def _run_libreoffice(content: bytes, filename: str, *, target: str) -> bytes:
    if not content:
        raise HTTPException(status_code=422, detail="Documento vazio.")
    executable, xvfb = _engine()
    extension = ".docx" if filename.lower().endswith(".docx") else ".doc"

    with tempfile.TemporaryDirectory(prefix="cti-doc-") as temp_dir:
        workdir = Path(temp_dir)
        source = workdir / f"source{extension}"
        source.write_bytes(content)
        profile_dir = workdir / "lo-profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        output_dir = workdir / "out"
        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            xvfb,
            "-a",
            "-s",
            "-screen 0 1280x1024x24",
            executable,
            "--headless",
            "--nologo",
            "--nodefault",
            "--nolockcheck",
            f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
        ]
        if extension == ".docx":
            command.append("--infilter=Office Open XML Text")
        command.extend([
            "--convert-to",
            target,
            "--outdir",
            str(output_dir.resolve()),
            str(source.resolve()),
        ])

        process_env = os.environ.copy()
        process_env["HOME"] = str(workdir.resolve())
        process_env["TMPDIR"] = str(workdir.resolve())
        process_env["SAL_USE_VCLPLUGIN"] = "svp"
        process_env.pop("DISPLAY", None)

        result = subprocess.run(
            command,
            cwd=str(workdir.resolve()),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            env=process_env,
        )
        diagnostics = " | ".join(
            parte.strip() for parte in (result.stderr, result.stdout) if parte and parte.strip()
        )
        if result.returncode != 0:
            raise HTTPException(status_code=422, detail=f"Conversão recusada: {(diagnostics or 'erro sem detalhe')[:800]}")

        output_extension = ".pdf" if target.startswith("pdf") else ".docx"
        output = output_dir / f"source{output_extension}"
        if not output.exists() or output.stat().st_size == 0:
            raise HTTPException(
                status_code=422,
                detail=f"O conversor não produziu o arquivo esperado. Detalhe: {(diagnostics or 'sem detalhe')[:800]}",
            )
        return output.read_bytes()


def _pdf_pages(pdf: bytes) -> int:
    try:
        return len(PdfReader(BytesIO(pdf)).pages)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"PDF inválido: {exc}") from exc


@app.get("/health")
def health() -> dict[str, object]:
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    xvfb = shutil.which("xvfb-run")
    return {
        "ok": bool(executable and xvfb),
        "engine": executable,
        "xvfb": xvfb,
        "expected_pages": EXPECTED_PAGES,
        "legacy_doc_to_docx": True,
        "source_aware_pagination": True,
    }


@app.post("/normalize-docx")
async def normalize_docx(
    file: UploadFile = File(...),
    x_cti_converter_key: str | None = Header(default=None),
) -> Response:
    _authorize(x_cti_converter_key)
    filename = Path(file.filename or "modelo.doc").name
    if not filename.lower().endswith(".doc") or filename.lower().endswith(".docx"):
        raise HTTPException(status_code=422, detail="A normalização aceita somente arquivos DOC legados.")
    content = await file.read()

    source_pdf = _run_libreoffice(content, filename, target="pdf:writer_pdf_Export")
    source_pages = _pdf_pages(source_pdf)
    if source_pages <= 0:
        raise HTTPException(status_code=422, detail="Não foi possível determinar a paginação do documento mestre.")

    docx = _run_libreoffice(content, filename, target="docx:Office Open XML Text")
    if not docx.startswith(b"PK"):
        raise HTTPException(status_code=422, detail="DOCX normalizado inválido.")
    return Response(
        content=docx,
        media_type=DOCX_MIME,
        headers={
            "Content-Disposition": f'inline; filename="{Path(filename).stem}.docx"',
            "X-CTI-SHA256": hashlib.sha256(docx).hexdigest(),
            "X-CTI-Source-Pages": str(source_pages),
            "Cache-Control": "no-store",
        },
    )


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    x_cti_converter_key: str | None = Header(default=None),
    x_cti_expected_pages: int | None = Header(default=None),
) -> Response:
    _authorize(x_cti_converter_key)
    filename = Path(file.filename or "proposta.docx").name
    if not filename.lower().endswith((".docx", ".doc")):
        raise HTTPException(status_code=422, detail="Formato de documento não suportado.")
    content = await file.read()
    pdf = _run_libreoffice(content, filename, target="pdf:writer_pdf_Export")
    pages = _pdf_pages(pdf)

    expected_pages = x_cti_expected_pages if x_cti_expected_pages and x_cti_expected_pages > 0 else EXPECTED_PAGES
    if pages != expected_pages:
        raise HTTPException(
            status_code=422,
            detail=f"PDF rejeitado: mestre oficial {expected_pages} páginas, gerado {pages}.",
        )

    output_name = f"{Path(filename).stem}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{output_name}"',
            "X-CTI-Pages": str(pages),
            "X-CTI-Expected-Pages": str(expected_pages),
            "X-CTI-SHA256": hashlib.sha256(pdf).hexdigest(),
            "Cache-Control": "no-store",
        },
    )
