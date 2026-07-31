from __future__ import annotations

import hashlib
import io
import mimetypes
import zipfile
from datetime import datetime, timezone
from pathlib import PurePosixPath

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.admin_auth import UsuarioAutenticado, exigir_escrita_catalogo
from core.supabase_client import supabase

router = APIRouter(prefix="/modelos-proposta-importacao", tags=["Modelos de proposta"])
BUCKET = "modelos-propostas-carrier"
MAX_PACKAGE_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".doc", ".docx"}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(valor: object) -> str:
    return "-".join(str(valor or "").strip().lower().split())


def _modelos_ativos() -> list[dict]:
    return (
        supabase.table("cti_modelos_proposta")
        .select("*")
        .eq("ativo", True)
        .not_.is_("arquivo_template_nome_original", "null")
        .order("linha_produto")
        .order("equipamento")
        .execute()
        .data
        or []
    )


@router.post("/pacote")
async def importar_pacote(
    pacote: UploadFile = File(...),
    usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo),
):
    nome_pacote = PurePosixPath(pacote.filename or "").name
    if not nome_pacote.lower().endswith(".zip"):
        raise HTTPException(status_code=422, detail="Envie um único pacote ZIP.")

    conteudo_pacote = await pacote.read()
    if not conteudo_pacote:
        raise HTTPException(status_code=422, detail="O pacote está vazio.")
    if len(conteudo_pacote) > MAX_PACKAGE_BYTES:
        raise HTTPException(status_code=413, detail="O pacote excede 20 MB.")

    try:
        arquivo_zip = zipfile.ZipFile(io.BytesIO(conteudo_pacote))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=422, detail="O arquivo enviado não é um ZIP válido.") from exc

    arquivos: dict[str, bytes] = {}
    for item in arquivo_zip.infolist():
        if item.is_dir():
            continue
        nome = PurePosixPath(item.filename).name
        extensao = PurePosixPath(nome).suffix.lower()
        if extensao not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail=f"Arquivo não permitido no pacote: {nome}")
        if nome in arquivos:
            raise HTTPException(status_code=422, detail=f"Nome duplicado no pacote: {nome}")
        arquivos[nome] = arquivo_zip.read(item)

    modelos = _modelos_ativos()
    esperados = {str(item.get("arquivo_template_nome_original") or "") for item in modelos}
    esperados.discard("")
    recebidos = set(arquivos)

    faltantes = sorted(esperados - recebidos)
    extras = sorted(recebidos - esperados)
    if faltantes or extras:
        raise HTTPException(
            status_code=422,
            detail={"mensagem": "O pacote não corresponde ao conjunto oficial.", "faltantes": faltantes, "extras": extras},
        )

    resultados: list[dict] = []
    falhas: list[dict] = []

    for modelo in modelos:
        modelo_id = str(modelo.get("id"))
        nome = str(modelo.get("arquivo_template_nome_original") or "")
        binario = arquivos[nome]
        hash_recebido = hashlib.sha256(binario).hexdigest().lower()
        hash_esperado = str(modelo.get("arquivo_template_hash_sha256") or "").lower()
        tamanho_esperado = int(modelo.get("arquivo_template_tamanho_bytes") or 0)

        if len(binario) != tamanho_esperado or hash_recebido != hash_esperado:
            falhas.append({"modelo_id": modelo_id, "arquivo": nome, "erro": "Tamanho ou SHA-256 divergente."})
            continue

        if modelo.get("arquivo_template_storage"):
            resultados.append({"modelo_id": modelo_id, "arquivo": nome, "situacao": "JA_ARMAZENADO"})
            continue

        versao = int(modelo.get("versao") or 1)
        caminho = f"{_slug(modelo.get('linha_produto'))}/{_slug(modelo.get('equipamento'))}/v{versao}/{nome}"
        mime = mimetypes.guess_type(nome)[0] or "application/octet-stream"

        try:
            supabase.storage.from_(BUCKET).upload(
                caminho,
                binario,
                {"content-type": mime, "upsert": "false"},
            )
            agora = _agora()
            atualizado = (
                supabase.table("cti_modelos_proposta")
                .update({
                    "arquivo_template_storage": caminho,
                    "homologado_em": None,
                    "layout_preservado": True,
                    "conteudo_integral_obrigatorio": True,
                    "imutavel": True,
                    "updated_at": agora,
                })
                .eq("id", modelo_id)
                .is_("arquivo_template_storage", "null")
                .execute()
                .data
                or []
            )
            if not atualizado:
                raise RuntimeError("Registro alterado por outro processo.")

            supabase.table("cti_modelos_proposta_auditoria").insert({
                "modelo_proposta_id": modelo_id,
                "operacao": "ATIVACAO",
                "versao": versao,
                "arquivo_template_storage": caminho,
                "arquivo_template_nome_original": nome,
                "arquivo_template_hash_sha256": hash_recebido,
                "conteudo_template": modelo.get("conteudo_template") or {},
                "justificativa": f"Importação única do pacote oficial por ADMIN_MASTER {usuario.email}; arquivo validado por nome, tamanho e SHA-256.",
            }).execute()
            resultados.append({"modelo_id": modelo_id, "arquivo": nome, "situacao": "ARMAZENADO", "caminho": caminho})
        except Exception as exc:
            falhas.append({"modelo_id": modelo_id, "arquivo": nome, "erro": str(exc)})

    return {
        "ok": not falhas,
        "arquivos_unicos_recebidos": len(arquivos),
        "modelos_processados": len(modelos),
        "armazenados_ou_existentes": len(resultados),
        "falhas": falhas,
        "resultados": resultados,
        "proxima_etapa": "FILA_HOMOLOGACAO_VISUAL",
    }
