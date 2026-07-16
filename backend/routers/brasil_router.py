from fastapi import APIRouter

from repositories.cti_repository import repository
from services.base_analytics import (
    consolidar_clientes,
    consolidar_dashboard,
    consolidar_implementadoras,
    consolidar_territorial,
)

router = APIRouter(prefix="/brasil")


def registros_brasil():
    return repository.buscar_por_origem("BRASIL")


@router.get("/dashboard")
def dashboard():
    return consolidar_dashboard(registros_brasil())


@router.get("/implementadoras")
def implementadoras():
    return consolidar_implementadoras(registros_brasil())


@router.get("/clientes")
def clientes():
    return consolidar_clientes(registros_brasil())


@router.get("/territorial")
def territorial():
    return consolidar_territorial(registros_brasil())
