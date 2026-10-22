from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import NotFound
from ...core.response import ApiResponse
from ...infra.db import get_session
from ...modules.jobs import service
from ...modules.jobs.models import Job
from ...modules.jobs.schemas import JobOut, JobPage

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=ApiResponse[JobPage])
async def list_jobs(
    city: str | None = Query(default=None, max_length=50),
    batch: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[JobPage]:
    items, total = await service.query_jobs(
        session,
        city=city,
        batch=batch,
        keyword=keyword,
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


@router.get("/{job_id}", response_model=ApiResponse[JobOut])
async def get_job(
    job_id: int, session: AsyncSession = Depends(get_session)
) -> ApiResponse[JobOut]:
    job = await session.get(Job, job_id)
    if job is None or job.status != "PUBLISHED":
        raise NotFound(f"job not found: {job_id}")
    return ApiResponse(data=JobOut.model_validate(job))
