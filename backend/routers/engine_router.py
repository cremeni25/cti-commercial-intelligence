from fastapi import APIRouter
from engine.market_engine import MarketEngine
from repositories.cti_repository import repository

router = APIRouter()

# ----------------------------------------
# TESTE BANCO
# ----------------------------------------

@router.get("/engine/test-db")
def test_db():

    return repository.buscar_amostra_cti_anfir(10)


# ----------------------------------------
# MARKET INTELLIGENCE
# ----------------------------------------

@router.get("/engine/market-intelligence")
def market_intelligence():

    data = repository.buscar_cti_anfir()

    engine = MarketEngine(data)

    return engine.market_intelligence()
