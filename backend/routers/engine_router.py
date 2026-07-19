from fastapi import APIRouter
from repositories.cti_repository import repository
from engine.market_engine import MarketEngine

router = APIRouter()


@router.get("/engine/test-db")
def test_db():
    return repository.buscar_cti_anfir()[:10]


@router.get("/engine/market-intelligence")
def market_intelligence():
    data = repository.buscar_cti_anfir()
    engine = MarketEngine(data)
    return engine.market_intelligence()
