from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import Conflict, NotFound
from .models import DictItem, DictType
from .schemas import DictItemCreate, DictItemUpdate, DictTypeCreate

SEED_DICTS: list[tuple[str, str, list[str]]] = [
    ("CITY", "城市", ["北京", "上海", "深圳", "杭州", "广州", "成都"]),
    ("BATCH", "届别", ["2026届", "2027届"]),
    ("CATEGORY", "职位类别", ["技术", "产品", "设计", "运营"]),
]


async def get_snapshot(session: AsyncSession) -> tuple[int, list[DictType]]:
    types = list(
        (
            await session.scalars(select(DictType).order_by(DictType.type_code))
        ).all()
    )
    version = max((t.version for t in types), default=0)
    return version, types


async def _get_type(session: AsyncSession, type_code: str) -> DictType:
    dtype = (
        await session.scalars(select(DictType).where(DictType.type_code == type_code))
    ).one_or_none()
    if dtype is None:
        raise NotFound(f"dict type not found: {type_code}")
    return dtype


async def create_type(session: AsyncSession, body: DictTypeCreate) -> DictType:
    exists = (
        await session.scalars(
            select(DictType.id).where(DictType.type_code == body.type_code)
        )
    ).first()
    if exists is not None:
        raise Conflict(f"dict type already exists: {body.type_code}")
    dtype = DictType(
        type_code=body.type_code, name=body.name, description=body.description
    )
    session.add(dtype)
    await session.commit()
    await session.refresh(dtype)
    return dtype


async def create_item(session: AsyncSession, body: DictItemCreate) -> DictItem:
    dtype = await _get_type(session, body.type_code)
    exists = (
        await session.scalars(
            select(DictItem.id).where(
                DictItem.type_id == dtype.id, DictItem.item_key == body.item_key
            )
        )
    ).first()
    if exists is not None:
        raise Conflict(f"dict item already exists: {body.type_code}/{body.item_key}")
    item = DictItem(
        type_id=dtype.id,
        item_key=body.item_key,
        item_value=body.item_value,
        sort_order=body.sort_order,
        enabled=body.enabled,
    )
    session.add(item)
    dtype.version += 1
    await session.commit()
    await session.refresh(item)
    return item


async def update_item(
    session: AsyncSession, item_id: int, body: DictItemUpdate
) -> DictItem:
    item = await session.get(DictItem, item_id)
    if item is None:
        raise NotFound(f"dict item not found: {item_id}")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    dtype = await session.get(DictType, item.type_id)
    if dtype is not None:
        dtype.version += 1
    await session.commit()
    await session.refresh(item)
    return item


async def delete_item(session: AsyncSession, item_id: int) -> None:
    item = await session.get(DictItem, item_id)
    if item is None:
        raise NotFound(f"dict item not found: {item_id}")
    dtype = await session.get(DictType, item.type_id)
    if dtype is not None:
        dtype.version += 1
    await session.delete(item)
    await session.commit()


async def ensure_seed_dicts(session: AsyncSession) -> int:
    created = 0
    for type_code, name, items in SEED_DICTS:
        exists = (
            await session.scalars(
                select(DictType.id).where(DictType.type_code == type_code)
            )
        ).first()
        if exists is not None:
            continue
        dtype = DictType(type_code=type_code, name=name)
        session.add(dtype)
        await session.flush()
        for idx, value in enumerate(items):
            session.add(
                DictItem(
                    type_id=dtype.id,
                    item_key=value,
                    item_value=value,
                    sort_order=idx,
                )
            )
        created += 1
    await session.commit()
    return created
