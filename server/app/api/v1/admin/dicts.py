from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.permissions import require_perm
from ....core.response import ApiResponse
from ....infra.db import get_session
from ....modules.dicts import service
from ....modules.dicts.schemas import (
    DictItemCreate,
    DictItemOut,
    DictItemUpdate,
    DictSnapshot,
    DictTypeCreate,
    DictTypeOut,
)

router = APIRouter(prefix="/dicts", dependencies=[Depends(require_perm("dict:manage"))])


@router.get("", response_model=ApiResponse[DictSnapshot])
async def list_dicts(session: AsyncSession = Depends(get_session)):
    current, types = await service.get_snapshot(session)
    return ApiResponse(
        data=DictSnapshot(
            version=current,
            types=[DictTypeOut.model_validate(t) for t in types],
        )
    )


@router.post("/types", status_code=201, response_model=ApiResponse[DictTypeOut])
async def create_type(
    body: DictTypeCreate, session: AsyncSession = Depends(get_session)
) -> ApiResponse[DictTypeOut]:
    dtype = await service.create_type(session, body)
    return ApiResponse(data=DictTypeOut.model_validate(dtype))


@router.post("/items", status_code=201, response_model=ApiResponse[DictItemOut])
async def create_item(
    body: DictItemCreate, session: AsyncSession = Depends(get_session)
) -> ApiResponse[DictItemOut]:
    item = await service.create_item(session, body)
    return ApiResponse(data=DictItemOut.model_validate(item))


@router.patch("/items/{item_id}", response_model=ApiResponse[DictItemOut])
async def update_item(
    item_id: int, body: DictItemUpdate, session: AsyncSession = Depends(get_session)
) -> ApiResponse[DictItemOut]:
    item = await service.update_item(session, item_id, body)
    return ApiResponse(data=DictItemOut.model_validate(item))


@router.delete("/items/{item_id}", response_model=ApiResponse[None])
async def delete_item(
    item_id: int, session: AsyncSession = Depends(get_session)
) -> ApiResponse[None]:
    await service.delete_item(session, item_id)
    return ApiResponse()
