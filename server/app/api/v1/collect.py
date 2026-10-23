"""采集接口：用户提交文本/URL，或上传 Excel/图片文件。"""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ...core.permissions import AuthSubject, require_perm
from ...core.response import ApiResponse
from ...modules.collect.schemas import CollectResult, CollectSubmit
from ...modules.collect.service import run_collect

router = APIRouter(prefix="/collect", tags=["collect"])


@router.post(
    "",
    response_model=ApiResponse[CollectResult],
    dependencies=[Depends(require_perm("task:create"))],
)
async def collect_text(
    body: CollectSubmit,
    subject: AuthSubject = Depends(require_perm("task:create")),
) -> ApiResponse[CollectResult]:
    """提交文本或网页 URL 进行采集。"""
    result = await run_collect(
        source_type=body.source_type,
        payload=body.content,
        source_url=body.content if body.source_type == "html" else None,
        created_by=subject.user_id,
    )
    return ApiResponse(data=result)


@router.post(
    "/upload",
    response_model=ApiResponse[CollectResult],
    dependencies=[Depends(require_perm("task:create"))],
)
async def collect_upload(
    source_type: str = Form(..., pattern="^(excel|image)$"),
    file: UploadFile = File(...),
    subject: AuthSubject = Depends(require_perm("task:create")),
) -> ApiResponse[CollectResult]:
    """上传 Excel 或图片文件进行采集。"""
    content = await file.read()
    result = await run_collect(
        source_type=source_type,
        payload=content,
        created_by=subject.user_id,
    )
    return ApiResponse(data=result)
