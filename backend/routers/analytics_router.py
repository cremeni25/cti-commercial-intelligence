from fastapi import APIRouter, Query

from repositories.cti_repository import repository
from services.base_analytics import consolidar_dashboard
from services.commercial_intelligence import consolidar_inteligencia

router = APIRouter()


def _registros_por_contexto(contexto: str):
    if contexto == "viena-sp":
        return repository.buscar_por_origem("VIENA_SP", "VIENA")
    if contexto == "outros-dealers":
        registros = repository.buscar_cti_anfir()
        return [
            registro
            for registro in registros
            if not (
                registro.get("origem_base") == "VIENA_SP"
                or registro.get("autorizado") == "VIENA"
            )
        ]
    return repository.buscar_cti_anfir()


@router.get("/analytics/dashboard")
def dashboard(contexto: str = Query("brasil", pattern="^(brasil|viena-sp)$")):
    return consolidar_dashboard(_registros_por_contexto(contexto))


@router.get("/analytics/intelligence")
def intelligence(
    contexto: str = Query("brasil", pattern="^(brasil|viena-sp|outros-dealers)$"),
    segmento: str = Query("GERAL", pattern="^(GERAL|TR|DT|DD|UNKNOWN)$"),
):
    return consolidar_inteligencia(
        _registros_por_contexto(contexto),
        contexto=contexto,
        segmento=segmento,
    )
