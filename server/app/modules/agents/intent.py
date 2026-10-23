"""意图识别（对话管理 Agent 的轻量理解层）：规则优先，可选 LLM 增强。"""

from __future__ import annotations

import re

import structlog

log = structlog.get_logger()

URL_RE = re.compile(r"https?://\S+")

# 规则按优先级排列：URL → 采集类 → 管理类 → 调度 → 画像 → 推荐 → 帮助
RULES: list[tuple[str, list[str]]] = [
    ("collect", ["采集", "抓取", "上传", "录入", "发布招聘", "招聘信息如下", "collect"]),
    ("jobinfo", ["过期", "清理", "下线", "去重", "职位统计", "职位管理"]),
    ("schedule", ["定时任务", "调度", "任务列表", "cron"]),
    ("profile", ["偏好", "画像", "我想找", "求职意向", "我的设置"]),
    ("recommend", ["推荐", "帮我找", "找职位", "有什么职位", "有哪些职位", "求推荐", "在招", "找工作"]),
    ("help", ["帮助", "help", "你能做什么", "怎么用", "指令"]),
]

VALID_LABELS = {"collect", "recommend", "profile", "jobinfo", "schedule", "help"}


def rule_intent(text: str) -> tuple[str, float]:
    """规则意图识别，返回 (intent, confidence)。"""
    if URL_RE.search(text):
        return "collect", 0.9
    lowered = text.lower()
    for intent, keywords in RULES:
        for kw in keywords:
            if kw in lowered:
                return intent, 0.8
    return "chat", 0.2


async def detect_intent(text: str, *, use_llm: bool = True) -> tuple[str, float]:
    """规则优先；未命中且配置了真实 LLM 时走模型分类，否则落到 help。"""
    intent, confidence = rule_intent(text)
    if intent != "chat" or not use_llm:
        return intent, confidence

    from .model_router import model_router  # 延迟导入避免环

    if model_router.provider_name == "mock":
        return "help", 0.3
    try:
        system = (
            "你是求职助手 JobClaw 的意图分类器。"
            "只输出一个词，从以下选择：collect/recommend/profile/jobinfo/schedule/help。"
        )
        result = await model_router.complete(task="intent", system=system, prompt=text)
        label = result.text.strip().lower().split()[0] if result.text.strip() else ""
        if label in VALID_LABELS:
            return label, 0.7
    except Exception as exc:  # noqa: BLE001
        log.warning("llm_intent_failed", error=str(exc))
    return "help", 0.3
