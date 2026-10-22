from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.response import ApiResponse
from ...infra.db import get_session
from ...modules.dicts import service
from ...modules.dicts.schemas import DictSnapshot, DictTypeOut

router = APIRouter(prefix="/dicts", tags=["dicts"])


@router.get("")
async def get_dicts(
    version: int | None = Query(default=None, ge=0),
    session: AsyncSession = Depends(get_session),
):
    current, types = await service.get_snapshot(session)
    if version is not None and version == current:
        return Response(status_code=304)
    return ApiResponse(
        data=DictSnapshot(
            version=current,
            types=[DictTypeOut.model_validate(t) for t in types],
        )
    )
