"""会话状态存储：架构要求 Redis，连接不可用时降级内存实现（测试友好）。"""

from __future__ import annotations

import json
import time
from typing import Any, Protocol

import structlog

from ...core.config import get_settings

log = structlog.get_logger()

SESSION_TTL = 1800  # 秒


class SessionStore(Protocol):
    async def get(self, key: str) -> dict[str, Any] | None: ...

    async def set(self, key: str, data: dict[str, Any], ttl: int = SESSION_TTL) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def close(self) -> None: ...


class InMemorySessionStore:
    """内存实现：单进程兜底 / 测试用。"""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, dict]] = {}

    def _purge(self) -> None:
        now = time.time()
        for key in [k for k, (exp, _) in self._data.items() if exp <= now]:
            self._data.pop(key, None)

    async def get(self, key: str) -> dict[str, Any] | None:
        self._purge()
        item = self._data.get(key)
        return dict(item[1]) if item else None

    async def set(self, key: str, data: dict[str, Any], ttl: int = SESSION_TTL) -> None:
        self._data[key] = (time.time() + ttl, dict(data))

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def close(self) -> None:
        self._data.clear()


class RedisSessionStore:
    """Redis 实现：架构要求的会话状态维护。"""

    def __init__(self, client) -> None:
        self._client = client
        self._prefix = "jobclaw:sess:"

    async def get(self, key: str) -> dict[str, Any] | None:
        raw = await self._client.get(self._prefix + key)
        return json.loads(raw) if raw else None

    async def set(self, key: str, data: dict[str, Any], ttl: int = SESSION_TTL) -> None:
        await self._client.set(
            self._prefix + key, json.dumps(data, ensure_ascii=False), ex=ttl
        )

    async def delete(self, key: str) -> None:
        await self._client.delete(self._prefix + key)

    async def close(self) -> None:
        await self._client.aclose()


_store: SessionStore | None = None


async def get_session_store() -> SessionStore:
    """惰性初始化：优先 Redis，不可用则降级内存。"""
    global _store
    if _store is not None:
        return _store
    url = get_settings().redis_url
    if url:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
            await client.ping()
            _store = RedisSessionStore(client)
            log.info("session_store_initialized", backend="redis")
            return _store
        except Exception as exc:  # noqa: BLE001
            log.warning("session_store_redis_unavailable", error=str(exc))
    _store = InMemorySessionStore()
    log.info("session_store_initialized", backend="memory")
    return _store


async def reset_session_store() -> None:
    """测试辅助：重置单例。"""
    global _store
    if _store is not None:
        await _store.close()
    _store = None
