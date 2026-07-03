from fastapi import APIRouter

from engine.cti_engine import cti_engine

router = APIRouter()


@router.get("/analytics/dashboard")
def dashboard():

    return cti_engine.analytics_dashboard()