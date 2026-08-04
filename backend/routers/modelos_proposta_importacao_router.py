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
from services.proposal_template_catalog import TEMPLATES

router = APIRouter(prefix="/modelos-proposta-importacao", tags=["Modelos de proposta"])
BUCKET = "modelos-propostas-carrier"
MAX_PACKAGE_BYTES = 30 * 1024 * 1024
ALLOWED_EXTENSIONS = {".doc", ".docx"}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(valor: object) -> str:
    return "-".join(str(valor or "").strip().lower().split())


def _linha_produto(equipamento: str) -> str:
    if equipamento.startswith("VECTOR") or equipamento.startswith("X4"):
        return "TRAILER"
    if equipamento.startswith("SUPRA") or equipamento in {"S8", "S9"}:
        return "DIESEL TRUCK"
    return "DIRECT DRIVE"


def _modelo_existente(equipamento: str, versao: int) -> dict | None:
    rows = (
        supabase.table("cti_modelos_proposta")
        .select("*")
        .eq("equipamento", equipamento)
        .eq("versao", versao)
        .limit(1)
        .execute()
        .data
        or []
    )
    return rows[0] if rows else None


def _arquivo_por_nome(arquivos: dict[str, bytes], nome_esperado: str) -> bytes | None:
    alvo = nome_esperado.casefold()
    encontrados = [conteudo for nome, conteudo in arquivos.items() if nome.casefold() == alvo]
    if len(encontrados) != 1:
        return None
    return encontrados[0]


def _registrar_auditoria(
    *,
    modelo: dict,
    equipamento: str,
    versao: int,
    caminho: str,
    nome_arquivo: str,
    hash_recebido: str,
    usuario_email: str,
) -> str | None:
    try:
        supabase.table("cti_modelos_proposta_auditoria").insert({
            "modelo_proposta_id": modelo.get("id"),
            "nome": equipamento,
            "operacao": "ATIVACAO",
            "versao": versao,
            "arquivo_template_storage": caminho,
            "arquivo_template_nome_original": nome_arquivo,
            "arquivo_template_hash_sha256": hash_recebido,
            "conteudo_template": modelo.get("conteudo_template") or {},
            "justificativa": (
                "Substituição controlada pelo pacote integral dos 16 documentos oficiais Carrier; "
                "binário preservado sem alteração, tamanho e SHA-256 calculados no recebimento; "
                f"executado por ADMIN_MASTER {usuario_email}."
            ),
        }).execute()
        return None
    except Exception as exc:
        return str(exc)


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
        raise HTTPException(status_code=413, detail="O pacote excede 30 MB.")

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
            continue
        chave = nome.casefold()
        if any(existente.casefold() == chave for existente in arquivos):
            raise HTTPException(status_code=422, detail=f"Nome duplicado no pacote: {nome}")
        arquivos[nome] = arquivo_zip.read(item)

    esperados = {template.source_filename for template in TEMPLATES}
    faltantes = sorted(
        nome for nome in esperados if not any(recebido.casefold() == nome.casefold() for recebido in arquivos)
    )
    extras = sorted(
        nome for nome in arquivos if not any(nome.casefold() == esperado.casefold() for esperado in esperados)
    )
    if faltantes or extras:
        raise HTTPException(
            status_code=422,
            detail={
                "mensagem": "O pacote não corresponde aos 16 documentos oficiais.",
                "faltantes": faltantes,
                "extras": extras,
            },
        )

    resultados: list[dict] = []
    falhas: list[dict] = []
    avisos_auditoria: list[dict] = []

    for template in TEMPLATES:
        binario = _arquivo_por_nome(arquivos, template.source_filename)
        if not binario:
            falhas.append({"equipamento": template.equipment, "erro": "Arquivo oficial não localizado no pacote."})
            continue

        hash_recebido = hashlib.sha256(binario).hexdigest().lower()
        tamanho = len(binario)
        versao = int(template.version)
        caminho = f"oficiais/{_slug(template.equipment)}/v{versao}/{template.source_filename}"
        mime = mimetypes.guess_type(template.source_filename)[0] or "application/octet-stream"
        agora = _agora()

        try:
            supabase.storage.from_(BUCKET).upload(
                caminho,
                binario,
                {"content-type": mime, "upsert": "true"},
            )

            existente = _modelo_existente(template.equipment, versao)
            registro = {
                "linha_produto": _linha_produto(template.equipment),
                "equipamento": template.equipment,
                "versao": versao,
                "arquivo_template_nome_original": template.source_filename,
                "arquivo_template_tamanho_bytes": tamanho,
                "arquivo_template_hash_sha256": hash_recebido,
                "arquivo_template_storage": caminho,
                "homologado_em": agora,
                "layout_preservado": True,
                "conteudo_integral_obrigatorio": True,
                "imutavel": True,
                "ativo": True,
                "updated_at": agora,
            }

            if existente:
                atualizado = (
                    supabase.table("cti_modelos_proposta")
                    .update(registro)
                    .eq("id", existente.get("id"))
                    .execute()
                    .data
                    or []
                )
                if not atualizado:
                    raise RuntimeError("O banco não confirmou a atualização do modelo oficial.")
                modelo = atualizado[0]
            else:
                registro["created_at"] = agora
                inseridos = supabase.table("cti_modelos_proposta").insert(registro).execute().data or []
                if not inseridos:
                    raise RuntimeError("O banco não confirmou a criação do modelo oficial.")
                modelo = inseridos[0]

            aviso = _registrar_auditoria(
                modelo=modelo,
                equipamento=template.equipment,
                versao=versao,
                caminho=caminho,
                nome_arquivo=template.source_filename,
                hash_recebido=hash_recebido,
                usuario_email=usuario.email,
            )
            if aviso:
                avisos_auditoria.append({"equipamento": template.equipment, "aviso": aviso})

            resultados.append({
                "modelo_id": modelo.get("id"),
                "equipamento": template.equipment,
                "arquivo": template.source_filename,
                "tamanho_bytes": tamanho,
                "sha256": hash_recebido,
                "situacao": "MESTRE_OFICIAL_ATUALIZADO",
            })
        except Exception as exc:
            falhas.append({"equipamento": template.equipment, "arquivo": template.source_filename, "erro": str(exc)})

    return {
        "ok": not falhas and len(resultados) == len(TEMPLATES),
        "arquivos_unicos_recebidos": len(arquivos),
        "modelos_esperados": len(TEMPLATES),
        "modelos_atualizados": len(resultados),
        "falhas": falhas,
        "avisos_auditoria": avisos_auditoria,
        "resultados": resultados,
        "proxima_etapa": "GERAR_PROPOSTA_PDF_COM_MESTRE_OFICIAL",
    }
