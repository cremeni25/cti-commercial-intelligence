from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.ia_agente_homologacao_config import carregar_ia_agente_homologacao_config
from routers.ia_comercial_agente_homologacao_router import router as ia_agente_router


config = carregar_ia_agente_homologacao_config()

if not config.pronta_para_homologacao:
    raise RuntimeError(
        "Backend de homologação bloqueado: exige CTI_AMBIENTE=homologation, "
        "CTI_IA_AGENTE_HOMOLOGACAO=true e CTI_IA_AGENTE_SOMENTE_LEITURA=true."
    )

app = FastAPI(
    title="CTI IA Comercial — Espelho de Homologação",
    version="0.1.0-homologacao",
    docs_url="/docs" if os.getenv("CTI_HOMOLOGACAO_DOCS", "false").lower() == "true" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origem.strip() for origem in os.getenv("CTI_HOMOLOGACAO_ORIGENS", "").split(",") if origem.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(ia_agente_router)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "servico": "cti-ia-agente-homologacao",
        "ambiente": config.ambiente,
        "somente_leitura_operacional": config.somente_leitura,
        "carrega_backend_cti_completo": False,
        "unificado_producao": False,
    }
