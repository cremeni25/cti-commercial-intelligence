from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, exigir_escrita_catalogo
from core.supabase_client import supabase
from routers.modelos_proposta_storage_router import (
    HomologacaoTemplate,
    _homologar_modelo,
    _modelo,
    _url_temporaria,
)

router = APIRouter(prefix="/modelos-proposta-homologacao", tags=["Modelos de proposta"])


class ItemHomologacao(BaseModel):
    modelo_id: str
    sha256_confirmado: str
    validacao_visual_integral: bool = True
    observacao: str | None = None


class LoteHomologacao(BaseModel):
    itens: list[ItemHomologacao] = Field(min_length=1, max_length=50)


@router.get("/fila")
def fila_homologacao(
    usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo),
):
    modelos = (
        supabase.table("cti_modelos_proposta")
        .select(
            "id,linha_produto,equipamento,versao,arquivo_template_nome_original,"
            "arquivo_template_tamanho_bytes,arquivo_template_hash_sha256,"
            "arquivo_template_storage,homologado_em,ativo"
        )
        .eq("ativo", True)
        .not_.is_("arquivo_template_storage", "null")
        .is_("homologado_em", "null")
        .order("linha_produto")
        .order("equipamento")
        .execute()
        .data
        or []
    )

    fila = []
    for modelo in modelos:
        caminho = str(modelo.get("arquivo_template_storage") or "")
        fila.append({
            **modelo,
            "url_temporaria": _url_temporaria(caminho, 900),
            "url_valida_por_segundos": 900,
            "situacao": "PENDENTE_VALIDACAO_VISUAL",
        })

    return {"total_pendente": len(fila), "fila": fila, "usuario": usuario.email}


@router.post("/homologar-lote")
def homologar_lote(
    dados: LoteHomologacao,
    usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo),
):
    ids = [item.modelo_id for item in dados.itens]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="O lote contém modelo duplicado.")

    resultados = []
    erros = []
    for item in dados.itens:
        try:
            modelo = _modelo(item.modelo_id)
            resultados.append(
                _homologar_modelo(
                    modelo,
                    HomologacaoTemplate(
                        sha256_confirmado=item.sha256_confirmado,
                        validacao_visual_integral=item.validacao_visual_integral,
                        observacao=item.observacao
                        or f"Homologação visual integral confirmada por ADMIN_MASTER {usuario.email}.",
                    ),
                )
            )
        except HTTPException as exc:
            erros.append({"modelo_id": item.modelo_id, "status_code": exc.status_code, "detail": exc.detail})

    return {
        "ok": not erros,
        "homologados": len(resultados),
        "falhas": len(erros),
        "resultados": resultados,
        "erros": erros,
    }
