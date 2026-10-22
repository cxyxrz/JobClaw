from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from .context import current_request_id

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Unified response envelope: {code, message, data, trace_id}."""

    code: int = 0
    message: str = "ok"
    data: T | None = None
    trace_id: str = Field(default_factory=current_request_id)
