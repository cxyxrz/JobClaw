from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import Unauthorized
from ...core.permissions import AuthSubject, current_subject
from ...infra.db import get_session
from .models import User


async def current_user(
    session: AsyncSession = Depends(get_session),
    subject: AuthSubject = Depends(current_subject),
) -> User:
    user = await session.get(User, subject.user_id)
    if user is None:
        raise Unauthorized("user no longer exists")
    return user
