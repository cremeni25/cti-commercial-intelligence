from __future__ import annotations

from fastapi import APIRouter

from routers.catalogo_comercial_router import CriarItemCatalogoRequest, criar_item_por_catalogo
from services.crm_oportunidade_resumo_service import sincronizar_resumo_oportunidade

router = APIRouter(prefix="/crm-app", tags=["CRM App"])


@router.post("/oportunidades/{oportunidade_id}/itens")
def criar_item_crm_app(oportunidade_id: str, dados: CriarItemCatalogoRequest):
    criado = criar_item_por_catalogo(oportunidade_id, dados)
    sincronizar_resumo_oportunidade(oportunidade_id)
    return criado


@router.post("/oportunidades/{oportunidade_id}/sincronizar-resumo")
def sincronizar_resumo_crm_app(oportunidade_id: str):
    return sincronizar_resumo_oportunidade(oportunidade_id)
