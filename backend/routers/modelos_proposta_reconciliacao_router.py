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


def reconciliar_modelos_com_storage(*, executor: str) -> dict[str, Any]:
    paths = _listar_arquivos()
    indice = _indice_por_nome(paths)
    criados: list[dict[str, Any]] = []
    atualizados: list[dict[str, Any]] = []
    existentes: list[dict[str, Any]] = []
    bloqueios: list[dict[str, Any]] = []

    for template in TEMPLATES:
        candidatos = indice.get(template.source_filename.casefold(), [])
        if not candidatos:
            bloqueios.append({
                "equipamento": template.equipment,
                "arquivo_esperado": template.source_filename,
                "erro": "Arquivo mestre oficial não localizado no bucket privado.",
            })
            continue
        if len(candidatos) > 1:
            bloqueios.append({
                "equipamento": template.equipment,
                "arquivo_esperado": template.source_filename,
                "erro": "Mais de um arquivo oficial com o mesmo nome foi localizado.",
                "candidatos": candidatos,
            })
            continue

        path = candidatos[0]
        tamanho, sha256 = _metadados_binarios(path)
        agora = _agora()
        existente = _registro_existente(template.equipment, template.version)

        if existente:
            caminho_atual = str(existente.get("arquivo_template_storage") or "")
            hash_atual = str(existente.get("arquivo_template_hash_sha256") or "").lower()
            nome_atual = str(existente.get("arquivo_template_nome_original") or "")
            if caminho_atual != path or hash_atual != sha256.lower() or nome_atual != template.source_filename:
                dados_atualizados = {
                    "arquivo_template_nome_original": template.source_filename,
                    "arquivo_template_tamanho_bytes": tamanho,
                    "arquivo_template_hash_sha256": sha256,
                    "arquivo_template_storage": path,
                    "homologado_em": None,
                    "updated_at": agora,
                }
                resposta = (
                    supabase.table("cti_modelos_proposta")
                    .update(dados_atualizados)
                    .eq("id", existente.get("id"))
                    .execute()
                    .data
                    or []
                )
                if not resposta:
                    bloqueios.append({
                        "equipamento": template.equipment,
                        "arquivo_esperado": template.source_filename,
                        "erro": "O banco não confirmou a correção do vínculo do modelo.",
                    })
                    continue
                supabase.table("cti_modelos_proposta_auditoria").insert({
                    "modelo_proposta_id": existente.get("id"),
                    "operacao": "CORRECAO_VINCULO_MESTRE",
                    "versao": template.version,
                    "arquivo_template_storage": path,
                    "arquivo_template_nome_original": template.source_filename,
                    "arquivo_template_hash_sha256": sha256,
                    "conteudo_template": existente.get("conteudo_template") or {},
                    "justificativa": (
                        "Vínculo restaurado para o arquivo mestre oficial original; "
                        f"tamanho e SHA-256 recalculados diretamente do binário por {executor}."
                    ),
                }).execute()
                atualizados.append({
                    "id": existente.get("id"),
                    "equipamento": template.equipment,
                    "arquivo_template_storage": path,
                    "arquivo_template_hash_sha256": sha256,
                })
            else:
                existentes.append({
                    "id": existente.get("id"),
                    "equipamento": template.equipment,
                    "versao": template.version,
                    "arquivo_template_storage": caminho_atual,
                    "homologado_em": existente.get("homologado_em"),
                })
            continue

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
        criados.append({
            "id": modelo.get("id"),
            "equipamento": template.equipment,
            "versao": template.version,
            "arquivo_template_storage": path,
            "arquivo_template_tamanho_bytes": tamanho,
            "arquivo_template_hash_sha256": sha256,
        })

    total_confirmado = len(existentes) + len(criados) + len(atualizados)
    return {
        "ok": not bloqueios and total_confirmado == len(TEMPLATES),
        "esperados": len(TEMPLATES),
        "existentes": len(existentes),
        "criados": len(criados),
        "atualizados": len(atualizados),
        "total_confirmado": total_confirmado,
        "registros_criados": criados,
        "registros_atualizados": atualizados,
        "bloqueios": bloqueios,
    }


@router.post("/sincronizar-storage")
def sincronizar_modelos_com_storage(
    usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo),
):
    return reconciliar_modelos_com_storage(executor=usuario.email)
