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
        extension = ".docx" if filename.lower().endswith(".docx") else ".doc"
        # O LibreOffice recebe um nome interno neutro para eliminar qualquer
        # interferência de nome comercial, espaços ou caracteres do documento.
        source = workdir / f"source{extension}"
        source.write_bytes(content)
        profile_dir = workdir / "lo-profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        output_dir = workdir / "out"
        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
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
            "pdf:writer_pdf_Export",
            "--outdir",
            str(output_dir.resolve()),
            str(source.resolve()),
        ])
        process_env = os.environ.copy()
        process_env["HOME"] = str(workdir.resolve())
        process_env["TMPDIR"] = str(workdir.resolve())
        process_env.setdefault("SAL_USE_VCLPLUGIN", "gen")
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
            parte.strip()
            for parte in (result.stderr, result.stdout)
            if parte and parte.strip()
        )
        if result.returncode != 0:
            detail = diagnostics or "erro sem detalhe"
            raise HTTPException(status_code=422, detail=f"Conversão recusada: {detail[:800]}")

        output = output_dir / "source.pdf"
        if not output.exists() or output.stat().st_size == 0:
            detail = diagnostics or "LibreOffice terminou sem gerar arquivo de saída."
            raise HTTPException(
                status_code=422,
                detail=f"O conversor não produziu o PDF esperado. Detalhe: {detail[:800]}",
            )

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
    output_name = f"{Path(filename).stem}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{output_name}"',
            "X-CTI-Pages": str(EXPECTED_PAGES),
            "X-CTI-SHA256": sha256,
            "Cache-Control": "no-store",
        },
    )
