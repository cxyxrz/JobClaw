"""采集服务：运行 LangGraph 图并返回结果。"""

from .errors import CollectError
from .graph import collect_graph
from .schemas import CollectResult


async def run_collect(
    *,
    source_type: str,
    payload: bytes | str,
    source_url: str | None = None,
    created_by: int | None = None,
) -> CollectResult:
    """执行一次采集流程，返回草稿结果。"""
    state = {
        "source_type": source_type,
        "payload": payload,
        "source_url": source_url,
        "created_by": created_by,
    }
    try:
        result = await collect_graph.ainvoke(state)
    except CollectError as exc:
        return CollectResult(
            status="ERROR",
            confidence=0.0,
            message=str(exc),
        )

    ex = result.get("extracted")
    return CollectResult(
        draft_id=result.get("draft_id"),
        status=result.get("status", "UNKNOWN"),
        confidence=result.get("confidence", 0.0),
        title=getattr(ex, "title", None),
        company=getattr(ex, "company", None),
        message="" if result.get("draft_id") else "重复或未入库",
    )
