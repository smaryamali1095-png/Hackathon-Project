from fastapi import APIRouter, Query
from services.risk_engine import calculate_risk_score, calculate_all_risk_scores

router = APIRouter(prefix="/risk", tags=["Risk Scores"])


@router.get("/calculate/{cnic}")
async def calculate_single_risk(
    cnic: str,
    force: bool = Query(False)
):
    return await calculate_risk_score(cnic, "All", force_recalculate=force)


@router.post("/calculate-all")
async def calculate_all_scores(
    force: bool = Query(False)
):
    return await calculate_all_risk_scores(force_recalculate=force)