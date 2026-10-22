from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.errors import NotFound
from ....core.permissions import require_perm
from ....core.response import ApiResponse
from ....infra.db import get_session
from ....modules.jobs import service
from ....modules.jobs.models import Job
from ....modules.jobs.schemas import JobCreate, JobOut, JobPage, JobUpdate

router = APIRouter(prefix="/jobs")


@router.get(
    "",
    response_model=ApiResponse[JobPage],
    dependencies=[Depends(require_perm("task:read"))],
)
async def list_all_jobs(
    city: str | None = Query(default=None, max_length=50),
    batch: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=100),
    status: str = Query(default="PUBLISHED", pattern="^(PUBLISHED|OFFLINE|ALL)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[JobPage]:
    items, total = await service.query_jobs(
        session,
        city=city,
        batch=batch,
        keyword=keyword,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        data=JobPage(
            items=[JobOut.model_validate(j) for j in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post(
    "",
    status_code=201,
    response_model=ApiResponse[JobOut],
    dependencies=[Depends(require_perm("job:publish"))],
)
async def create_job(
    body: JobCreate, session: AsyncSession = Depends(get_session)
) -> ApiResponse[JobOut]:
    job = Job(**body.model_dump(), published_at=datetime.now(timezone.utc))
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return ApiResponse(data=JobOut.model_validate(job))


@router.patch(
    "/{job_id}",
    response_model=ApiResponse[JobOut],
    dependencies=[Depends(require_perm("job:publish"))],
)
async def update_job(
    job_id: int, body: JobUpdate, session: AsyncSession = Depends(get_session)
) -> ApiResponse[JobOut]:
    job = await session.get(Job, job_id)
    if job is None:
        raise NotFound(f"job not found: {job_id}")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    await session.commit()
    await session.refresh(job)
    return ApiResponse(data=JobOut.model_validate(job))
