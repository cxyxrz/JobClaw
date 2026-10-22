import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import Unauthorized
from ...core.security import create_access_token, hash_password, verify_password
from .models import User

log = structlog.get_logger()

SEED_USERS: list[tuple[str, str, str]] = [
    ("admin", "admin123", "ADMIN"),
    ("demo", "demo123", "USER"),
]


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> tuple[str, int, User]:
    user = (
        await session.scalars(select(User).where(User.username == username))
    ).one_or_none()
    if user is None or not user.password_hash or not verify_password(password, user.password_hash):
        raise Unauthorized("invalid username or password")
    token, ttl = create_access_token(user.id, user.role)
    return token, ttl, user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def ensure_seed(session: AsyncSession) -> None:
    for username, password, role in SEED_USERS:
        exists = (
            await session.scalars(select(User.id).where(User.username == username))
        ).first()
        if exists is None:
            session.add(
                User(username=username, password_hash=hash_password(password), role=role)
            )
            log.info("seed_user_created", username=username, role=role)
