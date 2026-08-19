from fastapi import APIRouter
from repositories.cti_repository import repository

router = APIRouter()


@router.get("/engine/test-db")
def test_db():
    return repository.buscar_cti_anfir()[:10]


@router.get("/engine/market-intelligence")
def market_intelligence():
    # pandas/numpy entram em memória somente quando este endpoint analítico
    # específico é usado; não no bootstrap de todas as rotas do CTI.
    from engine.market_engine import MarketEngine

    data = repository.buscar_cti_anfir()
    engine = MarketEngine(data)
    return engine.market_intelligence()
