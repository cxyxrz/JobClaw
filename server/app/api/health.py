from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ..infra.db import get_sessionmaker

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict:
    return {"status": "alive"}


@router.get("/health/ready")
async def ready() -> JSONResponse:
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        return JSONResponse(status_code=200, content={"status": "ready", "db": "ok"})
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable", "db": "error"})
