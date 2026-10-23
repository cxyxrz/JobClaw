"""校招采集 Agent（业务）：接入 M2 采集流水线（LangGraph），支持文本/URL。"""

from __future__ import annotations

import re

import structlog

from ..collect.service import run_collect
from .base import AgentMessage, AgentReply, BaseAgent, register_agent
from .tools_agent import tools_agent

log = structlog.get_logger()

URL_RE = re.compile(r"https?://\S+")

GUIDE_TEXT = (
    "请把招聘信息原文粘贴给我，或直接发送网页链接；\n"
    "也可以在管理端「采集工作台」上传 Excel / 图片批量采集。"
)


async def run_text_collect(text: str, created_by: int | None = None):
    """文本直采（对话/调度共用）。"""
    return await run_collect(source_type="text", payload=text, created_by=created_by)


async def run_url_collect(url: str, created_by: int | None = None):
    """URL 采集：经工具调用 Agent 抓取正文 → 走文本采集流水线。"""
    fetched = await tools_agent.execute("web_fetch", {"url": url})
    text = fetched.get("text", "")
    if not text.strip():
        from ..collect.schemas import CollectResult

        return CollectResult(status="ERROR", confidence=0.0, message="网页正文为空")
    return await run_collect(
        source_type="text", payload=text, source_url=url, created_by=created_by
    )


def _format_result(result) -> str:
    if result.status == "ERROR":
        return f"采集失败：{result.message}"
    title = f"《{result.title}》" if result.title else ""
    company = f" - {result.company}" if result.company else ""
    conf = f"（置信度 {result.confidence:.0%}）" if result.confidence else ""
    if result.status == "DUPLICATE":
        return f"该职位已存在，未重复入库{title}{company}"
    if result.status == "REVIEW":
        return f"已采集{conf}，但置信度较低，已转入人工审核队列{title}{company}"
    if result.draft_id:
        return f"已生成草稿 #{result.draft_id}{conf}，可在管理端「草稿审核」确认后发布{title}{company}"
    return f"采集完成：{result.status} {title}{company}"


def _strip_command(text: str) -> str:
    for word in ("帮我采集", "采集一下", "采集", "抓取一下", "抓取", "上传", "录入"):
        text = text.replace(word, "")
    return text.strip()


@register_agent
class CollectAgent(BaseAgent):
    name = "collect"
    description = "校招采集：文本/URL 提交 → 解析抽取 → 去重入库草稿"

    async def handle(self, msg: AgentMessage) -> AgentReply:
        text = msg.text.strip()
        url_match = URL_RE.search(text)
        if url_match:
            url = url_match.group(0)
            try:
                result = await run_url_collect(url, msg.user_id)
            except Exception as exc:  # noqa: BLE001
                log.warning("collect_url_failed", url=url, error=str(exc))
                return AgentReply(
                    text=f"链接抓取失败：{exc}", agent=self.name, intent="collect"
                )
        else:
            body = _strip_command(text)
            if len(body) < 8:
                return AgentReply(text=GUIDE_TEXT, agent=self.name, intent="collect.guide")
            result = await run_text_collect(body, msg.user_id)
        return AgentReply(
            text=_format_result(result),
            agent=self.name,
            intent="collect",
            data=result.model_dump(),
        )
