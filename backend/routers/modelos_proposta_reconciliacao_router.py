from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, exigir_escrita_catalogo
from core.supabase_client import supabase
from services.proposal_template_catalog import TEMPLATES

router = APIRouter(prefix="/crm-documentos/modelos", tags=["Modelos oficiais Carrier"])

BUCKET = "modelos-propostas-carrier"
MAX_DEPTH = 8


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _listar_arquivos(path: str = "", depth: int = 0) -> list[str]:
    if depth > MAX_DEPTH:
        return []
    try:
        itens = supabase.storage.from_(BUCKET).list(path=path, options={"limit": 1000}) or []
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Não foi possível listar o bucket {BUCKET}: {exc}") from exc

    arquivos: list[str] = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        nome = str(item.get("name") or "").strip()
        if not nome:
            continue
        caminho = f"{path}/{nome}" if path else nome
        metadata = item.get("metadata")
        identificador = item.get("id")
        if metadata or identificador:
            arquivos.append(caminho)
        else:
            arquivos.extend(_listar_arquivos(caminho, depth + 1))
    return arquivos


def _indice_por_nome(paths: list[str]) -> dict[str, list[str]]:
    indice: dict[str, list[str]] = {}
    for path in paths:
        nome = PurePosixPath(path).name.casefold()
        indice.setdefault(nome, []).append(path)
    return indice


def _linha_produto(equipamento: str) -> str:
    if equipamento.startswith("VECTOR") or equipamento.startswith("X4"):
        return "TRAILER"
    if equipamento.startswith("SUPRA") or equipamento in {"S8", "S9", "CITIMAX D6", "CITIMAX D7"}:
        return "DIESEL TRUCK"
    return "DIRECT DRIVE"


def _registro_existente(equipamento: str, versao: int) -> dict[str, Any] | None:
    dados = (
        supabase.table("cti_modelos_proposta")
        .select("*")
        .eq("equipamento", equipamento)
        .eq("versao", versao)
        .limit(1)
        .execute()
        .data
        or []
    )
    return dados[0] if dados else None


def _metadados_binarios(path: str) -> tuple[int, str]:
    try:
        conteudo = supabase.storage.from_(BUCKET).download(path)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao baixar o arquivo mestre {path}: {exc}") from exc
    if not conteudo:
        raise HTTPException(status_code=409, detail=f"O arquivo mestre {path} está vazio.")
    raw = bytes(conteudo)
    return len(raw), hashlib.sha256(raw).hexdigest()


@router.post("/sincronizar-storage")
def sincronizar_modelos_com_storage(
    usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo),
):
    paths = _listar_arquivos()
    indice = _indice_por_nome(paths)
    criados: list[dict[str, Any]] = []
    existentes: list[dict[str, Any]] = []
    bloqueios: list[dict[str, Any]] = []

    for template in TEMPLATES:
        existente = _registro_existente(template.equipment, template.version)
        if existente:
            existentes.append({
                "id": existente.get("id"),
                "equipamento": template.equipment,
                "versao": template.version,
                "arquivo_template_storage": existente.get("arquivo_template_storage"),
                "homologado_em": existente.get("homologado_em"),
            })
            continue

        candidatos = indice.get(template.source_filename.casefold(), [])
        if not candidatos:
            bloqueios.append({
                "equipamento": template.equipment,
                "arquivo_esperado": template.source_filename,
                "erro": "Arquivo mestre não localizado no bucket privado.",
            })
            continue
        if len(candidatos) > 1:
            bloqueios.append({
                "equipamento": template.equipment,
                "arquivo_esperado": template.source_filename,
                "erro": "Mais de um arquivo com o mesmo nome foi localizado.",
                "candidatos": candidatos,
            })
            continue

        path = candidatos[0]
        tamanho, sha256 = _metadados_binarios(path)
        agora = _agora()
        registro = {
            "linha_produto": _linha_produto(template.equipment),
            "equipamento": template.equipment,
            "versao": template.version,
            "arquivo_template_nome_original": template.source_filename,
            "arquivo_template_tamanho_bytes": tamanho,
            "arquivo_template_hash_sha256": sha256,
            "arquivo_template_storage": path,
            "homologado_em": None,
            "layout_preservado": True,
            "conteudo_integral_obrigatorio": True,
            "imutavel": True,
            "ativo": True,
            "created_at": agora,
            "updated_at": agora,
        }
        inseridos = supabase.table("cti_modelos_proposta").insert(registro).execute().data or []
        if not inseridos:
            bloqueios.append({
                "equipamento": template.equipment,
                "arquivo_esperado": template.source_filename,
                "erro": "O banco não confirmou a criação do modelo.",
            })
            continue

        modelo = inseridos[0]
        supabase.table("cti_modelos_proposta_auditoria").insert({
            "modelo_proposta_id": modelo.get("id"),
            "operacao": "SINCRONIZACAO_STORAGE",
            "versao": template.version,
            "arquivo_template_storage": path,
            "arquivo_template_nome_original": template.source_filename,
            "arquivo_template_hash_sha256": sha256,
            "conteudo_template": modelo.get("conteudo_template") or {},
            "justificativa": (
                "Registro ausente criado a partir do arquivo mestre real já existente no bucket privado; "
                f"tamanho e SHA-256 calculados diretamente do binário por {usuario.email}."
            ),
        }).execute()
        criados.append({
            "id": modelo.get("id"),
            "equipamento": template.equipment,
            "versao": template.version,
            "arquivo_template_storage": path,
            "arquivo_template_tamanho_bytes": tamanho,
            "arquivo_template_hash_sha256": sha256,
        })

    total_confirmado = len(existentes) + len(criados)
    return {
        "ok": not bloqueios and total_confirmado == len(TEMPLATES),
        "esperados": len(TEMPLATES),
        "existentes": len(existentes),
        "criados": len(criados),
        "total_confirmado": total_confirmado,
        "registros_criados": criados,
        "bloqueios": bloqueios,
        "proxima_acao": (
            "Abrir a fila de homologação visual e homologar os modelos pendentes."
            if not bloqueios and total_confirmado == len(TEMPLATES)
            else "Disponibilizar no bucket somente os arquivos mestres listados nos bloqueios e executar novamente."
        ),
    }
