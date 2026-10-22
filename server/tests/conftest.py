import os
from collections.abc import AsyncIterator, Callable, Awaitable

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"
os.environ["SEED_ADMIN"] = "false"
os.environ["ENABLE_DEV_LOGIN"] = "true"
os.environ["LOG_JSON"] = "false"

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.infra.db import Base, dispose_db, get_engine, get_sessionmaker, init_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.modules.auth.models import User  # noqa: E402,F401


@pytest.fixture
async def client(tmp_path) -> AsyncIterator[AsyncClient]:
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    get_settings.cache_clear()
    init_db()
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c
    await dispose_db()
    get_settings.cache_clear()


@pytest.fixture
def make_user() -> Callable[[str, str, str], Awaitable[int]]:
    async def _make(username: str, password: str, role: str = "USER") -> int:
        async with get_sessionmaker()() as session:
            user = User(
                username=username, password_hash=hash_password(password), role=role
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user.id

    return _make
