from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, exigir_escrita_catalogo, exigir_leitura_catalogo
from services.product_catalog_service import criar_alias, criar_modelo, definir_ativo, listar_catalogo

router = APIRouter(prefix="/admin/product-catalog", tags=["Product Catalog"])


class ModelCreate(BaseModel):
    line_id: str
    canonical_name: str = Field(min_length=1, max_length=120)


class AliasCreate(BaseModel):
    alias: str = Field(min_length=1, max_length=120)
    model_id: str | None = None
    line_id: str | None = None


class ActiveUpdate(BaseModel):
    active: bool


@router.get("")
def get_catalog(_: UsuarioAutenticado = Depends(exigir_leitura_catalogo)):
    return listar_catalogo()


@router.post("/models", status_code=201)
def post_model(payload: ModelCreate, usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo)):
    try:
        return criar_modelo(payload.line_id, payload.canonical_name, usuario.email or usuario.nome)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Catálogo persistente indisponível: {exc}") from exc


@router.post("/aliases", status_code=201)
def post_alias(payload: AliasCreate, usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo)):
    try:
        return criar_alias(payload.alias, payload.model_id, payload.line_id, usuario.email or usuario.nome)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Catálogo persistente indisponível: {exc}") from exc


@router.patch("/lines/{entity_id}/active")
def patch_line_active(entity_id: str, payload: ActiveUpdate, usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo)):
    return _patch_active("cti_product_lines", "LINE", entity_id, payload.active, usuario)


@router.patch("/models/{entity_id}/active")
def patch_model_active(entity_id: str, payload: ActiveUpdate, usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo)):
    return _patch_active("cti_product_models", "MODEL", entity_id, payload.active, usuario)


@router.patch("/aliases/{entity_id}/active")
def patch_alias_active(entity_id: str, payload: ActiveUpdate, usuario: UsuarioAutenticado = Depends(exigir_escrita_catalogo)):
    return _patch_active("cti_product_aliases", "ALIAS", entity_id, payload.active, usuario)


def _patch_active(table: str, entity_type: str, entity_id: str, active: bool, usuario: UsuarioAutenticado):
    try:
        return definir_ativo(table, entity_type, entity_id, active, usuario.email or usuario.nome)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Catálogo persistente indisponível: {exc}") from exc
