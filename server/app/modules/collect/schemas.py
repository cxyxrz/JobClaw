from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None = None
    company: str | None = None
    city: str | None = None
    batch: str | None = None
    category: str | None = None
    salary_text: str | None = None
    description: str = ""
    source_url: str | None = None
    source_type: str
    confidence: float
    status: str
    review_note: str | None = None
    created_at: datetime


class DraftPage(BaseModel):
    items: list[DraftOut]
    total: int
    page: int
    page_size: int


class DraftReview(BaseModel):
    """管理员审核草稿：通过（转为正式职位）或拒绝。"""

    action: str = Field(pattern="^(accept|reject)$")
    note: str | None = Field(default=None, max_length=500)


class CollectSubmit(BaseModel):
    """提交采集任务。"""

    source_type: str = Field(pattern="^(text|html|excel|image)$")
    content: str = ""  # 文本直读 / 网页 URL
    # 二进制内容由上传接口处理，这里只接收文本类输入


class CollectResult(BaseModel):
    draft_id: int | None = None
    status: str
    confidence: float
    title: str | None = None
    company: str | None = None
    message: str = ""
