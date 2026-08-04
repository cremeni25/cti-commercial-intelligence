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

app = FastAPI(title="CTI Document Converter", version="1.0.0")
EXPECTED_PAGES = 4
API_KEY = os.getenv("CTI_DOCUMENT_CONVERTER_KEY", "").strip()


def _authorize(value: str | None) -> None:
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Chave do conversor não configurada.")
    if value != API_KEY:
        raise HTTPException(status_code=401, detail="Acesso não autorizado.")


@app.get("/health")
def health() -> dict[str, object]:
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    return {"ok": bool(executable), "engine": executable, "expected_pages": EXPECTED_PAGES}


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    x_cti_converter_key: str | None = Header(default=None),
) -> Response:
    _authorize(x_cti_converter_key)
    filename = Path(file.filename or "proposta.docx").name
    if not filename.lower().endswith((".docx", ".doc")):
        raise HTTPException(status_code=422, detail="Formato de documento não suportado.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Documento vazio.")

    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise HTTPException(status_code=503, detail="LibreOffice indisponível no serviço documental.")

    with tempfile.TemporaryDirectory(prefix="cti-doc-") as temp_dir:
        workdir = Path(temp_dir)
        source = workdir / filename
        source.write_bytes(content)
        command = [
            executable,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(workdir),
            str(source),
        ]
        result = subprocess.run(
            command,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro sem detalhe").strip()
            raise HTTPException(status_code=422, detail=f"Conversão recusada: {detail[:500]}")

        output = workdir / f"{source.stem}.pdf"
        if not output.exists() or output.stat().st_size == 0:
            raise HTTPException(status_code=422, detail="O conversor não produziu o PDF esperado.")

        pdf = output.read_bytes()
        try:
            pages = len(PdfReader(BytesIO(pdf)).pages)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"PDF inválido: {exc}") from exc
        if pages != EXPECTED_PAGES:
            raise HTTPException(
                status_code=422,
                detail=f"PDF rejeitado: esperado {EXPECTED_PAGES} páginas, gerado {pages}.",
            )

    sha256 = hashlib.sha256(pdf).hexdigest()
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{source.stem}.pdf"',
            "X-CTI-Pages": str(EXPECTED_PAGES),
            "X-CTI-SHA256": sha256,
            "Cache-Control": "no-store",
        },
    )
