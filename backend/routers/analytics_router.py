from fastapi import APIRouter, Query

from repositories.cti_repository import repository
from services.base_analytics import consolidar_dashboard

router = APIRouter()


def _registros_por_contexto(contexto: str):
    if contexto == "viena-sp":
        return repository.buscar_por_origem("VIENA_SP", "VIENA")
    return repository.buscar_cti_anfir()


@router.get("/analytics/dashboard")
def dashboard(contexto: str = Query("brasil", pattern="^(brasil|viena-sp)$")):
    return consolidar_dashboard(_registros_por_contexto(contexto))
