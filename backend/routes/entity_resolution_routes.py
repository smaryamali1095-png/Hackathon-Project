from fastapi import APIRouter, HTTPException

from services.entity_resolution_service import (
    run_entity_resolution,
    search_entity_matches,
    get_entity_comparison,
    merge_entity_match,
    flag_entity_match
)

router = APIRouter(
    prefix="/entity-resolution",
    tags=["Entity Resolution"]
)


@router.post("/run")
async def run_resolution():
    matches = await run_entity_resolution()
    return {
        "success": True,
        "total_matches": len(matches),
        "matches": matches
    }


@router.get("/matches")
async def get_matches(q: str = ""):
    matches = await search_entity_matches(q)
    return {
        "matches": matches
    }


@router.get("/comparison/{match_id}")
async def comparison(match_id: str):
    result = await get_entity_comparison(match_id)

    if not result:
        raise HTTPException(status_code=404, detail="Match not found")

    return result


@router.post("/merge/{match_id}")
async def merge_match(match_id: str):
    return await merge_entity_match(match_id)


@router.post("/flag/{match_id}")
async def flag_match(match_id: str):
    return await flag_entity_match(match_id)