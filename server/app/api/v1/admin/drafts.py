"""草稿管理：管理员查看采集草稿并审核（通过转正式职位 / 拒绝）。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.errors import NotFound
from ....core.permissions import require_perm
from ....core.response import ApiResponse
from ....infra.db import get_session
from ....modules.collect.models import JobDraft
from ....modules.collect.schemas import DraftOut, DraftPage, DraftReview
from ....modules.jobs.models import Job

router = APIRouter(prefix="/drafts")


@router.get(
    "",
    response_model=ApiResponse[DraftPage],
    dependencies=[Depends(require_perm("task:read"))],
)
async def list_drafts(
    status: str | None = Query(default=None, pattern="^(DRAFT|REVIEW|ACCEPTED|REJECTED)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[DraftPage]:
    stmt = select(JobDraft)
    if status:
        stmt = stmt.where(JobDraft.status == status)
    total = (
        await session.scalars(select(func.count()).select_from(stmt.subquery()))
    ).one()
    stmt = (
        stmt.order_by(JobDraft.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await session.scalars(stmt)).all())
    return ApiResponse(
        data=DraftPage(
            items=[DraftOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post(
    "/{draft_id}/review",
    response_model=ApiResponse[DraftOut],
    dependencies=[Depends(require_perm("draft:review"))],
)
async def review_draft(
    draft_id: int,
    body: DraftReview,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[DraftOut]:
    draft = await session.get(JobDraft, draft_id)
    if draft is None:
        raise NotFound(f"draft not found: {draft_id}")

    if body.action == "accept":
        # 转为正式职位
        job = Job(
            title=draft.title or "未命名职位",
            company=draft.company or "未知公司",
            city=draft.city or "未知",
            batch=draft.batch or "未知",
            category=draft.category,
            salary_text=draft.salary_text,
            description=draft.description,
            source_url=draft.source_url,
            published_at=datetime.now(timezone.utc),
        )
        session.add(job)
        draft.status = JobDraft.ACCEPTED
    else:
        draft.status = JobDraft.REJECTED

    draft.review_note = body.note
    await session.commit()
    await session.refresh(draft)
    return ApiResponse(data=DraftOut.model_validate(draft))
