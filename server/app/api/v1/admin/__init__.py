from fastapi import APIRouter, Depends

from ....core.permissions import AuthSubject, require_perm
from ....core.response import ApiResponse
from ....modules.auth.schemas import PingData
from . import dicts, drafts, jobs

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping", response_model=ApiResponse[PingData])
async def ping(
    subject: AuthSubject = Depends(require_perm("admin:ping")),
) -> ApiResponse[PingData]:
    return ApiResponse(data=PingData(pong=True, role=subject.role))


router.include_router(jobs.router)
router.include_router(dicts.router)
router.include_router(drafts.router)
