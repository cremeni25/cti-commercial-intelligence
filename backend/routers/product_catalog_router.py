from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from services.product_catalog_service import (
    criar_alias,
    criar_modelo,
    definir_ativo,
    listar_catalogo,
)

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
def get_catalog():
    return listar_catalogo()


@router.post("/models", status_code=201)
def post_model(payload: ModelCreate, x_cti_actor: str | None = Header(default=None)):
    try:
        return criar_modelo(payload.line_id, payload.canonical_name, x_cti_actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Catálogo persistente indisponível: {exc}") from exc


@router.post("/aliases", status_code=201)
def post_alias(payload: AliasCreate, x_cti_actor: str | None = Header(default=None)):
    try:
        return criar_alias(payload.alias, payload.model_id, payload.line_id, x_cti_actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Catálogo persistente indisponível: {exc}") from exc


@router.patch("/lines/{entity_id}/active")
def patch_line_active(entity_id: str, payload: ActiveUpdate, x_cti_actor: str | None = Header(default=None)):
    return _patch_active("cti_product_lines", "LINE", entity_id, payload.active, x_cti_actor)


@router.patch("/models/{entity_id}/active")
def patch_model_active(entity_id: str, payload: ActiveUpdate, x_cti_actor: str | None = Header(default=None)):
    return _patch_active("cti_product_models", "MODEL", entity_id, payload.active, x_cti_actor)


@router.patch("/aliases/{entity_id}/active")
def patch_alias_active(entity_id: str, payload: ActiveUpdate, x_cti_actor: str | None = Header(default=None)):
    return _patch_active("cti_product_aliases", "ALIAS", entity_id, payload.active, x_cti_actor)


def _patch_active(table: str, entity_type: str, entity_id: str, active: bool, actor: str | None):
    try:
        return definir_ativo(table, entity_type, entity_id, active, actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Catálogo persistente indisponível: {exc}") from exc
