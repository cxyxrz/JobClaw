"""校招采集 LangGraph 图：parse → extract → validate → dedupe → persist。"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from .errors import CollectError, PersistError, ValidateError
from .extractor import ExtractedJob, extract_fields
from .parsers.base import ParseResult
from .parsers.registry import get_parser

# 低置信度阈值：低于此值标为 REVIEW 需人工审核
CONFIDENCE_THRESHOLD = 0.6


class CollectState(TypedDict, total=False):
    source_type: str
    payload: bytes | str
    source_url: str | None
    created_by: int | None
    # 中间产物
    parsed: ParseResult
    extracted: ExtractedJob
    status: str
    confidence: float
    is_duplicate: bool
    draft_id: int | None
    error: str


async def parse_node(state: CollectState) -> CollectState:
    parser = get_parser(state["source_type"])
    parsed = await parser.parse(state["payload"], source_url=state.get("source_url"))
    return {"parsed": parsed}


def extract_node(state: CollectState) -> CollectState:
    text = state["parsed"].text
    extracted = extract_fields(text)
    return {"extracted": extracted, "confidence": extracted.confidence}


def validate_node(state: CollectState) -> CollectState:
    ex: ExtractedJob = state["extracted"]
    # 核心字段：title + company 必须存在，否则校验失败
    missing = []
    if not ex.title:
        missing.append("title")
    if not ex.company:
        missing.append("company")
    if missing:
        raise ValidateError(f"关键字段缺失: {', '.join(missing)}")
    return {"status": "ok"}


async def dedupe_node(state: CollectState) -> CollectState:
    """简单去重：同公司 + 同标题视为重复。"""
    from sqlalchemy import select

    from ...infra.db import get_sessionmaker
    from .models import JobDraft

    ex: ExtractedJob = state["extracted"]
    if not ex.company or not ex.title:
        return {"is_duplicate": False}

    async with get_sessionmaker()() as session:
        existing = await session.scalars(
            select(JobDraft).where(
                JobDraft.company == ex.company,
                JobDraft.title == ex.title,
            )
        )
        dup = existing.first() is not None
    return {"is_duplicate": dup}


async def persist_node(state: CollectState) -> CollectState:
    from ...infra.db import get_sessionmaker
    from .models import JobDraft

    ex: ExtractedJob = state["extracted"]
    parsed: ParseResult = state["parsed"]
    is_dup: bool = state.get("is_duplicate", False)
    conf: float = state.get("confidence", 0.0)

    # 重复则不入库
    if is_dup:
        return {"draft_id": None, "status": "DUPLICATE"}

    # 低置信度标 REVIEW
    status = JobDraft.REVIEW if conf < CONFIDENCE_THRESHOLD else JobDraft.DRAFT

    try:
        async with get_sessionmaker()() as session:
            draft = JobDraft(
                title=ex.title,
                company=ex.company,
                city=ex.city,
                batch=ex.batch,
                category=ex.category,
                salary_text=ex.salary_text,
                description=ex.description,
                source_url=state.get("source_url"),
                raw_text=parsed.text,
                source_type=parsed.source_type,
                confidence=conf,
                status=status,
                created_by=state.get("created_by"),
            )
            session.add(draft)
            await session.commit()
            await session.refresh(draft)
            return {"draft_id": draft.id, "status": status}
    except Exception as exc:  # noqa: BLE001
        raise PersistError(f"草稿入库失败: {exc}") from exc


def build_collect_graph():
    builder = StateGraph(CollectState)
    builder.add_node("parse", parse_node)
    builder.add_node("extract", extract_node)
    builder.add_node("validate", validate_node)
    builder.add_node("dedupe", dedupe_node)
    builder.add_node("persist", persist_node)

    builder.set_entry_point("parse")
    builder.add_edge("parse", "extract")
    builder.add_edge("extract", "validate")
    builder.add_edge("validate", "dedupe")
    builder.add_edge("dedupe", "persist")
    builder.add_edge("persist", END)
    return builder.compile()


collect_graph = build_collect_graph()
