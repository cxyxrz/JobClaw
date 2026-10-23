"""工具调用 Agent（支撑）：工具注册表 + 网页抓取 + 文件 IO + 搜索 + MCP 客户端。"""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import structlog

from ...core.config import get_settings
from ...core.errors import AppError, NotFound
from .base import AgentMessage, AgentReply, BaseAgent, register_agent

log = structlog.get_logger()


@dataclass(slots=True)
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Awaitable[Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]


async def _tool_web_fetch(url: str, timeout: int = 15) -> dict:
    """抓取网页并提取正文（trafilatura）。"""
    if not url.startswith(("http://", "https://")):
        raise AppError("url must start with http(s)://", code=40000, status_code=400)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text
    try:
        import trafilatura

        text = trafilatura.extract(html, include_comments=False) or ""
    except Exception:  # noqa: BLE001
        text = ""
    if not text.strip():
        text = re.sub(r"<[^>]+>", " ", html)[:3000]  # 兜底：去标签截断
    return {"url": url, "text": text[:5000], "fetched_at": datetime.now(UTC).isoformat()}


def _sandbox_root() -> Path:
    root = Path(get_settings().tool_sandbox_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _safe_path(filename: str) -> Path:
    """限制在沙箱目录内，防路径穿越。"""
    path = (_sandbox_root() / filename).resolve()
    if not str(path).startswith(str(_sandbox_root())):
        raise AppError("path escape detected", code=40000, status_code=400)
    return path


async def _tool_file_save(filename: str, content: str) -> dict:
    path = _safe_path(filename)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "size": len(content)}


async def _tool_file_read(filename: str) -> dict:
    path = _safe_path(filename)
    if not path.is_file():
        raise NotFound(f"file not found: {filename}")
    content = path.read_text(encoding="utf-8")
    return {"path": str(path), "content": content[:5000]}


async def _tool_search_web(query: str) -> dict:
    """搜索工具：配置 SEARCH_API_URL 后可用，否则返回未配置提示。"""
    url = get_settings().search_api_url
    if not url:
        return {"status": "not_configured", "message": "未配置搜索服务（SEARCH_API_URL）"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json={"query": query})
        resp.raise_for_status()
        return {"status": "ok", "result": resp.json()}


def _parse_mcp_body(resp: httpx.Response) -> dict:
    """兼容 JSON 与 SSE 两种 MCP 响应格式。"""
    if "text/event-stream" in resp.headers.get("content-type", ""):
        data_lines = [
            line[len("data: "):]
            for line in resp.text.splitlines()
            if line.startswith("data: ")
        ]
        payload: dict = {}
        for line in data_lines:
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    payload = parsed
            except json.JSONDecodeError:
                continue
        return payload
    return resp.json()


async def _tool_mcp_call(server_url: str, tool: str, arguments: dict | None = None) -> dict:
    """极简 MCP 客户端（Streamable HTTP 传输）：initialize → tools/call。"""
    headers = {"Accept": "application/json, text/event-stream"}
    async with httpx.AsyncClient(timeout=30) as client:
        init = await client.post(
            server_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "jobclaw", "version": "0.1.0"},
                },
            },
            headers=headers,
        )
        init.raise_for_status()
        session_id = init.headers.get("mcp-session-id")
        if session_id:
            headers["mcp-session-id"] = session_id
            await client.post(
                server_url,
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                headers=headers,
            )
        resp = await client.post(
            server_url,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments or {}},
            },
            headers=headers,
        )
        resp.raise_for_status()
        payload = _parse_mcp_body(resp)
    if "error" in payload:
        raise AppError(f"mcp error: {payload['error']}", code=50200, status_code=502)
    return payload.get("result", payload)


TOOL_SPECS = [
    Tool(
        name="web_fetch",
        description="抓取网页并提取正文文本",
        parameters={"url": "string, 必填", "timeout": "int, 秒, 默认15"},
        handler=_tool_web_fetch,
    ),
    Tool(
        name="file_save",
        description="保存文本文件到工具沙箱目录",
        parameters={"filename": "string", "content": "string"},
        handler=_tool_file_save,
    ),
    Tool(
        name="file_read",
        description="读取工具沙箱目录内的文本文件",
        parameters={"filename": "string"},
        handler=_tool_file_read,
    ),
    Tool(
        name="search_web",
        description="网页搜索（需配置搜索服务）",
        parameters={"query": "string"},
        handler=_tool_search_web,
    ),
    Tool(
        name="mcp_call",
        description="调用外部 MCP 服务器的工具（Streamable HTTP）",
        parameters={"server_url": "string", "tool": "string", "arguments": "object, 可选"},
        handler=_tool_mcp_call,
    ),
]


class ToolsAgent(BaseAgent):
    name = "tools"
    description = "工具调用：网页抓取 / 文件IO / 搜索 / MCP 客户端"

    def __init__(self) -> None:
        self.registry = ToolRegistry()
        for spec in TOOL_SPECS:
            self.registry.register(spec)

    async def execute(self, name: str, args: dict) -> Any:
        """供其他 Agent 编程调用（如采集 Agent 抓 URL）。"""
        tool = self.registry.get(name)
        if tool is None:
            raise NotFound(f"tool not found: {name}")
        return await tool.handler(**(args or {}))

    async def handle(self, msg: AgentMessage) -> AgentReply:
        text = msg.text.strip()
        if "工具列表" in text or text.lower() == "tools":
            lines = ["可用工具："]
            for t in self.registry.list():
                lines.append(f"· {t['name']} — {t['description']}")
            lines.append("调用格式：工具 web_fetch {{\"url\": \"https://...\"}}")
            return AgentReply(text="\n".join(lines), agent=self.name, intent="tools.list")

        m = re.match(r"工具\s+(\w+)\s*(\{.*\})?", text, re.DOTALL)
        if m:
            name = m.group(1)
            try:
                args = json.loads(m.group(2)) if m.group(2) else {}
                result = await self.execute(name, args)
                return AgentReply(
                    text=json.dumps(result, ensure_ascii=False, default=str)[:2000],
                    agent=self.name,
                    intent="tools.call",
                    data={"tool": name, "result": result},
                )
            except (json.JSONDecodeError, TypeError) as exc:
                return AgentReply(text=f"参数格式错误：{exc}", agent=self.name, intent="tools.call")

        return AgentReply(
            text="发送「工具列表」查看可用工具，或用「工具 web_fetch {\\\"url\\\": \\\"...\\\"}」调用。",
            agent=self.name,
            intent="tools.guide",
        )


tools_agent = register_agent(ToolsAgent())
