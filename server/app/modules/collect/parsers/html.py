"""网页解析器：使用 trafilatura 提取正文。"""

import httpx

from ..errors import ParseError
from .base import BaseParser, ParseResult


class HtmlParser(BaseParser):
    source_type = "html"

    async def parse(self, payload: bytes | str, **kwargs) -> ParseResult:
        # payload 可以是 URL 字符串，也可以是 HTML 字节串
        html: str
        source_url = kwargs.get("source_url")
        if isinstance(payload, str) and (
            payload.startswith("http://") or payload.startswith("https://")
        ):
            source_url = payload
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(payload)
                resp.raise_for_status()
                html = resp.text
        elif isinstance(payload, bytes):
            html = payload.decode("utf-8", errors="ignore")
        else:
            html = str(payload)

        try:
            import trafilatura

            text = trafilatura.extract(html, include_comments=False) or ""
        except Exception as exc:  # noqa: BLE001
            raise ParseError(f"网页正文提取失败: {exc}") from exc

        if not text.strip():
            raise ParseError("网页正文为空，无法提取职位信息")

        return ParseResult(text=text, source_type=self.source_type, meta={"source_url": source_url})
