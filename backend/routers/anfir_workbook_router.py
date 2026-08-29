from datetime import date

from fastapi import APIRouter

from repositories.cti_repository import repository
from services.anfir_workbook_contract import consolidar_workbook_anfir_2026
from services.operational_filters import filtrar_registros


router = APIRouter()


@router.get("/analytics/anfir-workbook-2026")
def anfif_workbook_2026():
    """Contrato funcional da auditoria ANFIR Carrier/JOV 2026.

    A leitura é deliberadamente fixa em Viena SP + competência 2026 para não
    misturar a fotografia auditada com filtros genéricos/históricos do CTI.
    Não grava nem altera qualquer registro.
    """
    base = repository.buscar_cti_anfir()
    registros = filtrar_registros(
        base,
        contexto="viena-sp",
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )
    return consolidar_workbook_anfir_2026(registros)
