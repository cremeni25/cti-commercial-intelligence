from fastapi import APIRouter
from core.supabase_client import supabase
from engine.market_engine import MarketEngine

router = APIRouter()

# ----------------------------------------
# TESTE BANCO
# ----------------------------------------

@router.get("/engine/test-db")
def test_db():

    response = supabase.table("cti_anfir").select("*").limit(10).execute()

    return response.data


# ----------------------------------------
# MARKET INTELLIGENCE
# ----------------------------------------

@router.get("/engine/market-intelligence")
def market_intelligence():

    response = supabase.table("cti_anfir").select("*").execute()

    data = response.data or []

    engine = MarketEngine(data)

    return engine.market_intelligence()
