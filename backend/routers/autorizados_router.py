from fastapi import APIRouter, HTTPException

from repositories.cti_repository import repository
from services.base_analytics import (
    consolidar_clientes,
    consolidar_dashboard,
    consolidar_historico,
    consolidar_implementadoras,
    consolidar_territorial,
)

router = APIRouter(prefix="/autorizados")

AUTORIZADOS = {
    "viena-sp": {
        "origem_base": "VIENA_SP",
        "autorizado": "VIENA",
    }
}


def contexto(slug):
    if slug not in AUTORIZADOS:
        raise HTTPException(status_code=404, detail="Autorizado não configurado")
    return AUTORIZADOS[slug]


def registros_autorizado(slug):
    cfg = contexto(slug)
    return repository.buscar_por_origem(cfg["origem_base"], cfg["autorizado"])


@router.get("/{slug}/dashboard")
def dashboard(slug: str):
    return consolidar_dashboard(registros_autorizado(slug))


@router.get("/{slug}/implementadoras")
def implementadoras(slug: str):
    return consolidar_implementadoras(registros_autorizado(slug))


@router.get("/{slug}/clientes")
def clientes(slug: str):
    return consolidar_clientes(registros_autorizado(slug))


@router.get("/{slug}/territorial")
def territorial(slug: str):
    return consolidar_territorial(registros_autorizado(slug))


@router.get("/{slug}/historico")
def historico(slug: str):
    return consolidar_historico(registros_autorizado(slug))
