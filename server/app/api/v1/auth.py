from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings
from ...core.errors import Forbidden
from ...core.response import ApiResponse
from ...infra.db import get_session
from ...modules.auth import service
from ...modules.auth.deps import current_user
from ...modules.auth.models import User
from ...modules.auth.schemas import LoginData, LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[LoginData])
async def login(
    body: LoginRequest, session: AsyncSession = Depends(get_session)
) -> ApiResponse[LoginData]:
    if not get_settings().enable_dev_login:
        raise Forbidden("password login is disabled in this environment")
    token, ttl, user = await service.authenticate(session, body.username, body.password)
    return ApiResponse(
        data=LoginData(
            access_token=token, expires_in=ttl, user=UserOut.model_validate(user)
        )
    )


@router.get("/me", response_model=ApiResponse[UserOut])
async def me(user: User = Depends(current_user)) -> ApiResponse[UserOut]:
    return ApiResponse(data=UserOut.model_validate(user))
