"""模型路由 Agent（基础设施层）：多模型切换 + Token 用量统计。

Provider 抽象：mock（规则兜底，零外部依赖）与 openai（OpenAI 兼容接口，
DeepSeek/通义等均可）。配置 LLM_PROVIDER=openai 且有 key 时自动启用，
失败自动回落 mock，保证可用性。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
import structlog
from sqlalchemy import func, select

from ...core.config import get_settings
from ...infra.db import get_sessionmaker
from .models import ModelUsage

log = structlog.get_logger()


def _estimate_tokens(text: str) -> int:
    """粗略估算 token 数（中文≈1字/token，混合按 0.5 计）。"""
    return max(1, len(text) // 2)


@dataclass(slots=True)
class LLMResult:
    text: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int


class BaseProvider(ABC):
    name: str = "base"
    model: str = ""

    @abstractmethod
    async def complete(self, *, system: str, prompt: str) -> LLMResult:
        raise NotImplementedError


class MockProvider(BaseProvider):
    """规则提供者：返回空文本，调用方自行兜底。"""

    name = "mock"
    model = "rule-based"

    async def complete(self, *, system: str, prompt: str) -> LLMResult:
        return LLMResult(
            text="",
            provider=self.name,
            model=self.model,
            prompt_tokens=_estimate_tokens(system + prompt),
            completion_tokens=0,
        )


class OpenAICompatProvider(BaseProvider):
    """OpenAI 兼容 Chat Completions 提供者。"""

    name = "openai"

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model = model

    async def complete(self, *, system: str, prompt: str) -> LLMResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
        usage = data.get("usage") or {}
        return LLMResult(
            text=(data["choices"][0]["message"]["content"] or "").strip(),
            provider=self.name,
            model=self.model,
            prompt_tokens=int(
                usage.get("prompt_tokens") or _estimate_tokens(system + prompt)
            ),
            completion_tokens=int(usage.get("completion_tokens") or 0),
        )


class ModelRouter:
    """按任务路由到模型提供者，并记录每次调用 Token 用量。"""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {"mock": MockProvider()}
        self._default = "mock"
        self._configured = False

    def configure(self) -> None:
        """根据配置装配提供者（幂等）。"""
        settings = get_settings()
        if settings.llm_provider == "openai" and settings.llm_api_key:
            self._providers["openai"] = OpenAICompatProvider(
                settings.llm_base_url, settings.llm_api_key, settings.llm_model
            )
            self._default = "openai"
        else:
            self._default = "mock"
        self._configured = True

    @property
    def provider_name(self) -> str:
        return self._default

    async def complete(self, *, task: str, system: str, prompt: str) -> LLMResult:
        if not self._configured:
            self.configure()
        provider = self._providers.get(self._default) or self._providers["mock"]
        try:
            result = await provider.complete(system=system, prompt=prompt)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "llm_provider_failed_fallback_mock", provider=provider.name, error=str(exc)
            )
            result = await self._providers["mock"].complete(system=system, prompt=prompt)
        await self._record_usage(task, result)
        return result

    async def _record_usage(self, task: str, result: LLMResult) -> None:
        try:
            async with get_sessionmaker()() as session:
                session.add(
                    ModelUsage(
                        provider=result.provider,
                        model=result.model,
                        task_type=task,
                        prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens,
                    )
                )
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            log.warning("model_usage_record_failed", error=str(exc))

    async def usage_stats(self) -> list[dict]:
        """按 提供者/模型/任务 聚合用量。"""
        async with get_sessionmaker()() as session:
            rows = await session.execute(
                select(
                    ModelUsage.provider,
                    ModelUsage.model,
                    ModelUsage.task_type,
                    func.count().label("calls"),
                    func.sum(ModelUsage.prompt_tokens).label("prompt_tokens"),
                    func.sum(ModelUsage.completion_tokens).label("completion_tokens"),
                ).group_by(ModelUsage.provider, ModelUsage.model, ModelUsage.task_type)
            )
            return [dict(row._mapping) for row in rows]


model_router = ModelRouter()
